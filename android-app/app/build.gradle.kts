plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.mysqlidle.mobile"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.mysqlidle.mobile"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "3.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}
