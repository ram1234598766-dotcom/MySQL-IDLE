package com.mysqlidle.mobile

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import android.webkit.SslErrorHandler
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebChromeClient
import android.net.http.SslError
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ImageView
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {
    private val prefs by lazy { getSharedPreferences("mysql_idle_mobile", MODE_PRIVATE) }
    private var root: LinearLayout? = null
    private var web: WebView? = null
    private var baseUri: Uri? = null
    private val blue = Color.rgb(37, 99, 235)
    private val ink = Color.rgb(15, 23, 42)
    private val muted = Color.rgb(100, 116, 139)
    private val paper = Color.rgb(248, 250, 252)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = paper
        window.navigationBarColor = paper
        window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
        showConnectScreen()
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private fun label(text: String, size: Float, color: Int = ink): TextView =
        TextView(this).apply {
            this.text = text
            textSize = size
            setTextColor(color)
        }

    private fun button(text: String, onClick: () -> Unit): Button =
        Button(this).apply {
            this.text = text
            isAllCaps = false
            setTextColor(Color.WHITE)
            backgroundTintList = android.content.res.ColorStateList.valueOf(blue)
            setOnClickListener { onClick() }
        }

    private fun showConnectScreen(error: String? = null) {
        web?.stopLoading()
        web?.let { (it.parent as? ViewGroup)?.removeView(it); it.destroy() }
        web = null
        baseUri = null

        val scroll = ScrollView(this)
        val page = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(28), dp(24), dp(28))
            setBackgroundColor(paper)
        }
        scroll.addView(page)
        setContentView(scroll)

        val brandHeader = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        brandHeader.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_mysqlidle_brandmark)
            contentDescription = "MySQL IDLE logo"
        }, LinearLayout.LayoutParams(dp(64), dp(64)))
        val brandText = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(14), 0, 0, 0)
        }
        brandText.addView(label("MySQL IDLE", 27f).apply {
            setTypeface(null, android.graphics.Typeface.BOLD)
        })
        brandText.addView(label("Mobile companion", 16f, blue).apply {
            setPadding(0, dp(2), 0, 0)
        })
        brandHeader.addView(brandText)
        page.addView(brandHeader, LinearLayout.LayoutParams(-1, -2).apply {
            bottomMargin = dp(28)
        })
        page.addView(label("Connect to the desktop companion", 19f).apply {
            setTypeface(null, android.graphics.Typeface.BOLD)
        })
        page.addView(label(
            "Start MySQL IDLE on your computer, open Tools → Android / Mobile Companion, " +
                "then enter the address shown by the desktop app.",
            14f, muted
        ).apply { setPadding(0, dp(8), 0, dp(18)) })

        page.addView(label("Desktop companion URL", 14f).apply {
            setTypeface(null, android.graphics.Typeface.BOLD)
        })
        val address = EditText(this).apply {
            hint = "http://192.168.1.10:8765"
            setSingleLine(true)
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_URI
            imeOptions = EditorInfo.IME_ACTION_GO
            setText(prefs.getString("server_url", ""))
            setPadding(dp(12), dp(10), dp(12), dp(10))
            setBackgroundColor(Color.WHITE)
        }
        page.addView(address, LinearLayout.LayoutParams(-1, dp(56)).apply {
            topMargin = dp(8)
            bottomMargin = dp(14)
        })
        if (error != null) {
            page.addView(label(error, 14f, Color.rgb(185, 28, 28)).apply {
                setPadding(0, 0, 0, dp(10))
            })
        }
        page.addView(button("Connect", onClick = { connect(address.text.toString()) }),
            LinearLayout.LayoutParams(-1, dp(52)).apply { bottomMargin = dp(22) })

        page.addView(label("Network security", 16f).apply {
            setTypeface(null, android.graphics.Typeface.BOLD)
        })
        page.addView(label(
            "This app opens your desktop's mobile companion inside a WebView. The local HTTP " +
                "connection is not encrypted. Use a trusted private Wi-Fi network only; never " +
                "publish or port-forward the companion to the public internet. Pairing is handled " +
                "by the desktop companion. This app does not save your MySQL password.",
            13f, muted
        ).apply { setPadding(0, dp(8), 0, dp(18)) })
        page.addView(label("Tip: allow the desktop application through your private-network firewall.",
            13f, muted))
    }

    private fun connect(raw: String) {
        val text = raw.trim().trimEnd('/')
        val parsed = runCatching { java.net.URI(text) }.getOrNull()
        if (parsed == null || parsed.scheme?.lowercase() !in listOf("http", "https") ||
            parsed.host.isNullOrBlank() || parsed.rawUserInfo != null ||
            parsed.rawPath !in listOf("", "/") || parsed.rawQuery != null ||
            parsed.rawFragment != null || (parsed.port != -1 && parsed.port !in 1..65535)) {
            showConnectScreen(
                "Enter the desktop root URL, such as http://192.168.1.10:8765, " +
                    "without a path, query, fragment or username."
            )
            return
        }
        val uri = Uri.parse(parsed.toASCIIString())
        baseUri = uri
        prefs.edit().putString("server_url", text).apply()
        showWebView(uri)
    }

    private fun showWebView(uri: Uri) {
        val page = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(paper)
        }
        root = page

        val browser = WebView(this)
        web = browser

        val toolbar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(8), dp(4), dp(8), dp(4))
            setBackgroundColor(Color.WHITE)
        }
        toolbar.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_mysqlidle_brandmark)
            contentDescription = "MySQL IDLE logo"
        }, LinearLayout.LayoutParams(dp(34), dp(34)).apply {
            marginEnd = dp(6)
        })
        toolbar.addView(button("Server", onClick = { showConnectScreen() }),
            LinearLayout.LayoutParams(dp(78), dp(46)))
        toolbar.addView(label(uri.host ?: uri.toString(), 13f, muted).apply {
            maxLines = 1
            ellipsize = android.text.TextUtils.TruncateAt.END
            setPadding(dp(8), 0, dp(4), 0)
        }, LinearLayout.LayoutParams(0, -2, 1f))
        val refreshButton = button("Refresh") { browser.reload() }.apply {
            contentDescription = "Refresh desktop companion"
        }
        toolbar.addView(refreshButton, LinearLayout.LayoutParams(dp(82), dp(46)))
        page.addView(toolbar)

        val loadingBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100
            progress = 0
            visibility = View.VISIBLE
            progressTintList = android.content.res.ColorStateList.valueOf(blue)
            contentDescription = "Page loading progress"
        }
        page.addView(loadingBar, LinearLayout.LayoutParams(-1, dp(3)))
        val loadingStatus = label("Connecting to desktop companion…", 12f, muted).apply {
            setPadding(dp(12), dp(6), dp(12), dp(6))
        }
        page.addView(loadingStatus, LinearLayout.LayoutParams(-1, -2))

        browser.setBackgroundColor(Color.WHITE)
        browser.settings.javaScriptEnabled = true
        browser.settings.domStorageEnabled = true
        browser.settings.allowFileAccess = false
        browser.settings.allowContentAccess = false
        browser.settings.javaScriptCanOpenWindowsAutomatically = false
        browser.settings.setSupportMultipleWindows(false)
        browser.settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW
        var pageLoadFailed = false
        browser.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView, newProgress: Int) {
                loadingBar.progress = newProgress
                if (!pageLoadFailed && newProgress < 100) {
                    loadingBar.visibility = View.VISIBLE
                    loadingStatus.visibility = View.VISIBLE
                    loadingStatus.text = "Loading desktop companion… $newProgress%"
                } else if (!pageLoadFailed) {
                    loadingBar.visibility = View.GONE
                    loadingStatus.visibility = View.GONE
                }
            }
        }
        browser.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView, url: String?, favicon: android.graphics.Bitmap?) {
                pageLoadFailed = false
                loadingBar.progress = 0
                loadingBar.visibility = View.VISIBLE
                loadingStatus.text = "Connecting to desktop companion…"
                loadingStatus.visibility = View.VISIBLE
                refreshButton.isEnabled = false
            }

            override fun onPageFinished(view: WebView, url: String?) {
                refreshButton.isEnabled = true
                if (!pageLoadFailed) {
                    loadingBar.visibility = View.GONE
                    loadingStatus.visibility = View.GONE
                }
            }
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val target = request.url
                val base = baseUri
                if (base != null && target.scheme == base.scheme &&
                    target.host == base.host && target.port == base.port) {
                    return false
                }
                return try {
                    startActivity(Intent(Intent.ACTION_VIEW, target))
                    true
                } catch (_: Exception) {
                    Toast.makeText(this@MainActivity, "Unable to open this link.", Toast.LENGTH_SHORT).show()
                    true
                }
            }

            override fun onReceivedSslError(view: WebView, handler: SslErrorHandler, error: SslError) {
                handler.cancel()
                pageLoadFailed = true
                loadingBar.visibility = View.GONE
                loadingStatus.text = "Secure connection failed certificate checks. Verify the URL and certificate, then refresh."
                loadingStatus.visibility = View.VISIBLE
                refreshButton.isEnabled = true
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: android.webkit.WebResourceError
            ) {
                if (request.isForMainFrame) {
                    pageLoadFailed = true
                    loadingBar.visibility = View.GONE
                    loadingStatus.text = "Could not reach the desktop companion. Check Wi-Fi, address and firewall, then tap Refresh."
                    loadingStatus.visibility = View.VISIBLE
                    refreshButton.isEnabled = true
                }
            }
        }
        page.addView(browser, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(page)
        browser.loadUrl(uri.toString())
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        val current = web
        if (current != null && current.canGoBack()) current.goBack()
        else showConnectScreen()
    }

    override fun onDestroy() {
        web?.stopLoading()
        web?.destroy()
        web = null
        super.onDestroy()
    }
}
