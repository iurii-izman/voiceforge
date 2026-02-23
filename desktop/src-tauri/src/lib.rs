//! VoiceForge desktop: Tauri + D-Bus client for com.voiceforge.App

const DBUS_NAME: &str = "com.voiceforge.App";
const DBUS_PATH: &str = "/com/voiceforge/App";
const DBUS_INTERFACE: &str = "com.voiceforge.App";

async fn connection() -> Result<zbus::Connection, String> {
    zbus::Connection::session().await.map_err(|e| e.to_string())
}

async fn call_method0(conn: &zbus::Connection, method: &str) -> Result<String, String> {
    let reply = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some(DBUS_INTERFACE),
            method,
            &(),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// Ping the daemon. Returns "pong" if daemon is available.
#[tauri::command]
pub async fn ping() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "Ping").await
}

/// GetSettings: returns raw JSON string (envelope with data.settings when VOICEFORGE_IPC_ENVELOPE=1).
#[tauri::command]
pub async fn get_settings() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetSettings").await
}

/// GetSessions(limit): returns raw JSON string (envelope with data.sessions when envelope on).
#[tauri::command]
pub async fn get_sessions(limit: u32) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some(DBUS_INTERFACE),
            "GetSessions",
            &(limit,),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// GetSessionDetail(session_id): returns raw JSON (envelope data.session_detail).
#[tauri::command]
pub async fn get_session_detail(session_id: u32) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some(DBUS_INTERFACE),
            "GetSessionDetail",
            &(session_id,),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// GetAnalytics(period): e.g. "7d", "30d". Returns raw JSON (envelope data.analytics).
#[tauri::command]
pub async fn get_analytics(period: String) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some(DBUS_INTERFACE),
            "GetAnalytics",
            &(period.as_str(),),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// IsListening: returns true if recording is active.
#[tauri::command]
pub async fn is_listening() -> Result<bool, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some(DBUS_INTERFACE),
            "IsListening",
            &(),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: bool = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// ListenStart: start ring-buffer recording. No return.
#[tauri::command]
pub async fn listen_start() -> Result<(), String> {
    let conn = connection().await?;
    conn.call_method(
        Some(DBUS_NAME),
        DBUS_PATH,
        Some(DBUS_INTERFACE),
        "ListenStart",
        &(),
    )
    .await
    .map_err(|e| e.to_string())?;
    Ok(())
}

/// ListenStop: stop recording. No return.
#[tauri::command]
pub async fn listen_stop() -> Result<(), String> {
    let conn = connection().await?;
    conn.call_method(
        Some(DBUS_NAME),
        DBUS_PATH,
        Some(DBUS_INTERFACE),
        "ListenStop",
        &(),
    )
    .await
    .map_err(|e| e.to_string())?;
    Ok(())
}

/// Analyze(seconds, template): run pipeline. Returns envelope with text or error.
#[tauri::command]
pub async fn analyze(seconds: u32, template: Option<String>) -> Result<String, String> {
    let conn = connection().await?;
    let t = template.unwrap_or_default();
    let reply = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some(DBUS_INTERFACE),
            "Analyze",
            &(seconds, t.as_str()),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// GetStreamingTranscript: partial + finals when recording (polling).
#[tauri::command]
pub async fn get_streaming_transcript() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetStreamingTranscript").await
}

/// Export session via CLI: voiceforge export --id <id> --format <md|pdf>. Returns path or error.
#[tauri::command]
pub async fn export_session(session_id: u32, format: String) -> Result<String, String> {
    let fmt = format.to_lowercase();
    if fmt != "md" && fmt != "pdf" {
        return Err("format must be md or pdf".to_string());
    }
    let output = std::process::Command::new("voiceforge")
        .args(["export", "--id", &session_id.to_string(), "--format", &fmt])
        .output()
        .map_err(|e| e.to_string())?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(stderr.to_string());
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.trim().to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            ping,
            get_settings,
            get_sessions,
            get_session_detail,
            get_analytics,
            is_listening,
            listen_start,
            listen_stop,
            analyze,
            get_streaming_transcript,
            export_session,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
