//! Tauri commands (D-Bus bridge).

use std::time::Duration;

use tauri::{Emitter, Manager};
use tokio::process::Command;

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

/// KC9: Return JSON array of indexed source paths from RAG DB.
#[tauri::command]
pub async fn get_indexed_paths() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetIndexedPaths").await
}

/// KC9: Return JSON { indexed_sources_count, chunks_count }.
#[tauri::command]
pub async fn get_rag_stats() -> Result<String, String> {
    let conn = connection().await?;
    call_method0(&conn, "GetRagStats").await
}

/// KC9: Index file/dir paths (JSON array of path strings). Returns JSON { ok, errors }.
#[tauri::command]
pub async fn index_paths(paths_json: String) -> Result<String, String> {
    let conn = connection().await?;
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "IndexPaths",
            &(paths_json.as_str(),),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// KC11: Set system audio opt-in (consent + optional PipeWire monitor source). Persisted on daemon.
#[tauri::command]
pub async fn set_system_audio_opt_in(consent_given: bool, monitor_source: Option<String>) -> Result<String, String> {
    let conn = connection().await?;
    let src = monitor_source.unwrap_or_default();
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "SetSystemAudioOptIn",
            &(consent_given, src.as_str()),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

/// KC12: On-demand answer refinement (deep/rewrite/tone). Returns JSON { refined, cost_usd } or { error }.
#[tauri::command]
pub async fn refine_copilot_answer(
    transcript: String,
    context: String,
    answer_text: String,
    mode: String,
    tone: Option<String>,
) -> Result<String, String> {
    let conn = connection().await?;
    let tone_str = tone.unwrap_or_default();
    let reply = conn
        .call_method(
            Some(crate::DBUS_NAME),
            crate::DBUS_PATH,
            Some(crate::DBUS_INTERFACE),
            "RefineCopilotAnswer",
            &(
                transcript.as_str(),
                context.as_str(),
                answer_text.as_str(),
                mode.as_str(),
                tone_str.as_str(),
            ),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
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

// --- RCP-M2: Daemon lifecycle commands (#196) ---

/// Check daemon status: D-Bus ping + systemctl state + structured Status() if reachable.
#[tauri::command]
pub async fn daemon_status() -> Result<String, String> {
    let mut daemon_reachable = false;
    let mut details: Option<String> = None;

    if let Ok(conn) = connection().await {
        let ping_ok = tokio::time::timeout(
            Duration::from_secs(2),
            call_method0(&conn, "Ping"),
        )
        .await
        .map(|r| r.is_ok())
        .unwrap_or(false);
        if ping_ok {
            daemon_reachable = true;
            if let Ok(s) = tokio::time::timeout(
                Duration::from_secs(2),
                call_method0(&conn, "Status"),
            )
            .await
            {
                details = s.ok();
            }
        }
    }

    let unit_installed = Command::new("systemctl")
        .args(["--user", "cat", "voiceforge.service"])
        .output()
        .await
        .map(|o| o.status.success())
        .unwrap_or(false);

    let unit_state = Command::new("systemctl")
        .args(["--user", "is-active", "voiceforge.service"])
        .output()
        .await
        .ok()
        .map(|o| {
            let s = String::from_utf8_lossy(if o.stdout.is_empty() { &o.stderr } else { &o.stdout });
            let t = s.trim();
            if t.is_empty() {
                "unknown".to_string()
            } else {
                t.to_string()
            }
        })
        .unwrap_or_else(|| "unknown".to_string());

    let out = serde_json::json!({
        "daemon_reachable": daemon_reachable,
        "unit_installed": unit_installed,
        "unit_state": unit_state,
        "details": details,
    });
    Ok(out.to_string())
}

/// Start daemon via systemctl --user start voiceforge.service; poll D-Bus Ping up to 10s.
#[tauri::command]
pub async fn daemon_start() -> Result<String, String> {
    let output = Command::new("systemctl")
        .args(["--user", "start", "voiceforge.service"])
        .output()
        .await
        .map_err(|e| format!("Failed to run systemctl: {e}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("systemctl start failed: {stderr}"));
    }

    for _ in 0..20 {
        tokio::time::sleep(Duration::from_millis(500)).await;
        if let Ok(conn) = connection().await {
            if tokio::time::timeout(
                Duration::from_secs(2),
                call_method0(&conn, "Ping"),
            )
            .await
            .map(|r| r.is_ok())
            .unwrap_or(false)
            {
                return Ok(r#"{"started": true}"#.to_string());
            }
        }
    }
    Ok(r#"{"started": false, "error": "Daemon started but not reachable via D-Bus after 10s"}"#.to_string())
}

/// Stop daemon via systemctl --user stop voiceforge.service.
#[tauri::command]
pub async fn daemon_stop() -> Result<String, String> {
    let output = Command::new("systemctl")
        .args(["--user", "stop", "voiceforge.service"])
        .output()
        .await
        .map_err(|e| format!("Failed to run systemctl: {e}"))?;
    if output.status.success() {
        Ok(r#"{"stopped": true}"#.to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("systemctl stop failed: {stderr}"))
    }
}

/// Restart daemon via systemctl --user restart; poll D-Bus Ping up to 10s.
#[tauri::command]
pub async fn daemon_restart() -> Result<String, String> {
    let output = Command::new("systemctl")
        .args(["--user", "restart", "voiceforge.service"])
        .output()
        .await
        .map_err(|e| format!("Failed to run systemctl: {e}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("systemctl restart failed: {stderr}"));
    }

    for _ in 0..20 {
        tokio::time::sleep(Duration::from_millis(500)).await;
        if let Ok(conn) = connection().await {
            if tokio::time::timeout(
                Duration::from_secs(2),
                call_method0(&conn, "Ping"),
            )
            .await
            .map(|r| r.is_ok())
            .unwrap_or(false)
            {
                return Ok(r#"{"restarted": true}"#.to_string());
            }
        }
    }
    Ok(r#"{"restarted": false, "error": "Daemon restarted but not reachable via D-Bus after 10s"}"#.to_string())
}

/// Run Doctor() D-Bus method; return structured health report JSON.
#[tauri::command]
pub async fn run_doctor() -> Result<String, String> {
    let conn = connection().await?;
    let result = tokio::time::timeout(
        Duration::from_secs(2),
        call_method0(&conn, "Doctor"),
    )
    .await
    .map_err(|_| "Doctor() timed out after 2s".to_string())?
    .map_err(|e| e.to_string())?;
    Ok(result)
}

/// Install systemd user service unit (voiceforge install-service).
#[tauri::command]
pub async fn install_service() -> Result<String, String> {
    let output = Command::new("voiceforge")
        .args(["install-service"])
        .output()
        .await
        .map_err(|e| format!("Failed to run install-service: {e}"))?;
    if output.status.success() {
        Ok(r#"{"installed": true}"#.to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("install-service failed: {stderr}"))
    }
}

/// Check if systemd user unit voiceforge.service is installed.
#[tauri::command]
pub async fn is_service_installed() -> Result<bool, String> {
    let output = Command::new("systemctl")
        .args(["--user", "cat", "voiceforge.service"])
        .output()
        .await
        .map_err(|e| format!("systemctl cat failed: {e}"))?;
    Ok(output.status.success())
}

/// Get recent daemon logs from journalctl (JSON output).
#[tauri::command]
pub async fn get_daemon_logs(lines: Option<u32>) -> Result<String, String> {
    let n = lines.unwrap_or(100);
    let output = Command::new("journalctl")
        .args([
            "--user",
            "-u",
            "voiceforge.service",
            "--no-pager",
            "-n",
            &n.to_string(),
            "-o",
            "json",
        ])
        .output()
        .await
        .map_err(|e| format!("Failed to read logs: {e}"))?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

/// Open the system default terminal with the given command (e.g. journalctl -f).
/// Tries xdg-terminal-exec, then gnome-terminal, konsole, xfce4-terminal, xterm.
#[tauri::command]
pub async fn open_terminal_with_command(command: String) -> Result<(), String> {
    let try_spawn = |prog: &str, args: &[&str]| -> std::io::Result<_> {
        Command::new(prog).args(args).spawn()
    };
    if try_spawn("xdg-terminal-exec", &["bash", "-c", &command]).is_ok() {
        return Ok(());
    }
    if try_spawn("gnome-terminal", &["--", "bash", "-c", &command]).is_ok() {
        return Ok(());
    }
    if try_spawn("konsole", &["-e", "bash", "-c", &command]).is_ok() {
        return Ok(());
    }
    let xfce_cmd = format!("bash -c {}", escape_shell_arg(&command));
    if try_spawn("xfce4-terminal", &["-e", &xfce_cmd]).is_ok() {
        return Ok(());
    }
    if try_spawn("xterm", &["-e", "bash", "-c", &command]).is_ok() {
        return Ok(());
    }
    Err("No terminal found (tried xdg-terminal-exec, gnome-terminal, konsole, xfce4-terminal, xterm)".to_string())
}

fn escape_shell_arg(s: &str) -> String {
    format!("'{}'", s.replace('\'', "'\"'\"'"))
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
