//! Tauri commands (D-Bus bridge).

use tauri::{Emitter, Manager};

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
pub async fn get_daemon_version() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetVersion").await
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
pub async fn get_session_ids_with_action_items() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetSessionIdsWithActionItems").await
}

#[tauri::command]
pub async fn search_transcripts(query: String, limit: u32) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "SearchTranscripts",
            &(query.as_str(), limit),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
pub async fn search_rag(query: String, limit: u32) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "SearchRag",
            &(query.as_str(), limit),
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

/// KC3: Start copilot push-to-capture (ensure listen, set marker, 30s auto-stop).
#[tauri::command]
pub async fn capture_start() -> Result<(), String> {
    let conn = connection().await?;
    conn.call_method(
        Some(crate::DBUS_NAME),
        crate::DBUS_PATH,
        Some(crate::DBUS_INTERFACE),
        "CaptureStart",
        &(),
    )
    .await
    .map_err(|e| e.to_string())?;
    Ok(())
}

/// KC3: End capture segment, extract with pre-roll, run analyze (returns immediately; AnalysisDone signal when done).
#[tauri::command]
pub async fn capture_release() -> Result<(), String> {
    let conn = connection().await?;
    conn.call_method(
        Some(crate::DBUS_NAME),
        crate::DBUS_PATH,
        Some(crate::DBUS_INTERFACE),
        "CaptureRelease",
        &(),
    )
    .await
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn get_copilot_capture_status() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetCopilotCaptureStatus").await
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
pub async fn get_upcoming_calendar_events() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetUpcomingEvents").await
}

/// Create a CalDAV event from a VoiceForge session (block 79, #95). calendar_url empty = first calendar.
#[tauri::command]
pub async fn create_event_from_session(session_id: u32, calendar_url: Option<String>) -> Result<String, String> {
    let conn = connection().await?;
    let url = calendar_url.unwrap_or_default();
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "CreateEventFromSession",
            &(session_id, url.as_str()),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
pub async fn set_tray_theme(app: tauri::AppHandle, is_dark: bool) -> Result<(), String> {
    crate::tray::set_tray_theme(&app, is_dark).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn export_session(session_id: u32, format: String) -> Result<String, String> {
    let fmt = format.to_lowercase();
    if fmt != "md" && fmt != "pdf" && fmt != "docx" && fmt != "notion" && fmt != "otter" {
        return Err("format must be md, pdf, docx, notion or otter".to_string());
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

/// KC2: Show copilot overlay and set state (armed | recording | analyzing | error). No focus steal.
#[tauri::command]
pub async fn set_copilot_overlay_state(
    app: tauri::AppHandle,
    state: String,
    show: bool,
) -> Result<(), String> {
    let Some(win) = app.get_webview_window("copilot-overlay") else {
        return Err("copilot-overlay window not found".to_string());
    };
    if show {
        // Position bottom-right of primary monitor (no focus).
        if let Ok(Some(monitor)) = win.current_monitor() {
            let size = monitor.size();
            let scale = monitor.scale_factor();
            let width = 400.0_f64;
            let height = 300.0_f64;
            let margin = 24.0_f64;
            let x = (size.width as f64 / scale) - width - margin;
            let y = (size.height as f64 / scale) - height - margin;
            let _ = win.set_position(tauri::Position::Logical(tauri::LogicalPosition { x, y }));
        }
        let _ = win.show();
        // Do not call set_focus() — overlay must not steal focus (KC2 contract).
    }
    let payload = serde_json::json!({ "state": state });
    win.emit("copilot-state-changed", payload).map_err(|e: tauri::Error| e.to_string())?;
    Ok(())
}
