//! Tauri commands (D-Bus bridge).

use crate::{call_method0, connection};

#[tauri::command]
pub async fn ping() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "Ping").await
}

#[tauri::command]
pub async fn get_settings() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetSettings").await
}

#[tauri::command]
pub async fn get_sessions(limit: u32) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "GetSessions",
            &(limit,),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
pub async fn get_session_detail(session_id: u32) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "GetSessionDetail",
            &(session_id,),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
pub async fn get_analytics(period: String) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "GetAnalytics",
            &(period.as_str(),),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
pub async fn is_listening() -> Result<bool, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "IsListening",
            &(),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: bool = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
pub async fn listen_start() -> Result<(), String> {
    let conn = connection().await?;
    conn.call_method(
        Some(crate::DBUS_NAME),
        crate::DBUS_PATH,
        Some(crate::DBUS_INTERFACE),
        "ListenStart",
        &(),
    )
    .await
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn listen_stop() -> Result<(), String> {
    let conn = connection().await?;
    conn.call_method(
        Some(crate::DBUS_NAME),
        crate::DBUS_PATH,
        Some(crate::DBUS_INTERFACE),
        "ListenStop",
        &(),
    )
    .await
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn analyze(seconds: u32, template: Option<String>) -> Result<String, String> {
    let conn = connection().await?;
    let t = template.unwrap_or_default();
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "Analyze",
            &(seconds, t.as_str()),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
pub async fn get_streaming_transcript() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetStreamingTranscript").await
}

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
