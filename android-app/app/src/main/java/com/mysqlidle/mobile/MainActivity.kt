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

        page.addView(label("MySQL IDLE", 30f).apply { setTypeface(null, android.graphics.Typeface.BOLD) })
        page.addView(label("Mobile companion", 17f, blue).apply {
            setPadding(0, dp(4), 0, dp(20))
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
        val uri = runCatching { Uri.parse(text) }.getOrNull()
        if (uri == null || uri.scheme !in listOf("http", "https") ||
            uri.host.isNullOrBlank() || uri.userInfo != null) {
            showConnectScreen("Enter a valid http:// or https:// desktop companion URL.")
            return
        }
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

        val toolbar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(8), dp(4), dp(8), dp(4))
            setBackgroundColor(Color.WHITE)
        }
        toolbar.addView(button("Server", onClick = { showConnectScreen() }),
            LinearLayout.LayoutParams(dp(92), dp(46)))
        toolbar.addView(label(uri.host ?: uri.toString(), 13f, muted).apply {
            maxLines = 1
            ellipsize = android.text.TextUtils.TruncateAt.END
            setPadding(dp(10), 0, 0, 0)
        }, LinearLayout.LayoutParams(0, -2, 1f))
        page.addView(toolbar)

        val browser = WebView(this)
        web = browser
        browser.setBackgroundColor(Color.WHITE)
        browser.settings.javaScriptEnabled = true
        browser.settings.domStorageEnabled = true
        browser.settings.allowFileAccess = false
        browser.settings.allowContentAccess = false
        browser.settings.javaScriptCanOpenWindowsAutomatically = false
        browser.settings.setSupportMultipleWindows(false)
        browser.settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW
        browser.webChromeClient = WebChromeClient()
        browser.webViewClient = object : WebViewClient() {
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
                Toast.makeText(this@MainActivity, "Secure connection failed certificate checks.", Toast.LENGTH_LONG).show()
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: android.webkit.WebResourceError
            ) {
                if (request.isForMainFrame) {
                    Toast.makeText(this@MainActivity,
                        "Could not reach desktop companion. Check Wi-Fi, URL and firewall.",
                        Toast.LENGTH_LONG).show()
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
