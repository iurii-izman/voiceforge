//! RCP #203: Version history tracking for rollback.
//! Metadata in ~/.local/share/<app>/versions/ (current.json, backups/).

use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Manager};

const VERSIONS_DIR: &str = "versions";
const CURRENT_JSON: &str = "current.json";
const BACKUPS_DIR: &str = "backups";
const MAX_BACKUP_MB: u64 = 500;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VersionMetadata {
    pub version: String,
    pub installed_at: String,
    pub path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub previous_version: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub backup_path: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub backup_size_mb: Option<f64>,
}

fn app_data_dir(app: &AppHandle) -> Result<PathBuf, String> {
    app.path().app_data_dir().map_err(|e| e.to_string())
}

pub fn backups_dir(app: &AppHandle) -> Result<PathBuf, String> {
    let base = app_data_dir(app)?;
    let dir = base.join(VERSIONS_DIR).join(BACKUPS_DIR);
    std::fs::create_dir_all(&dir).map_err(|e| format!("Cannot create backup dir: {e}"))?;
    Ok(dir)
}

fn current_json_path(app: &AppHandle) -> Result<PathBuf, String> {
    let base = app_data_dir(app)?;
    Ok(base.join(VERSIONS_DIR).join(CURRENT_JSON))
}

pub fn read_version_metadata(app: &AppHandle) -> Result<VersionMetadata, String> {
    let path = current_json_path(app)?;
    if !path.exists() {
        return Err("No version metadata found".to_string());
    }
    let s = std::fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&s).map_err(|e| e.to_string())
}

/// Write version metadata (e.g. before update: backup of current version).
pub fn save_version_metadata(
    app: &AppHandle,
    version: &str,
    exe_path: &Path,
    backup_path: Option<&Path>,
    previous_version: Option<&str>,
) -> Result<(), String> {
    let base = app_data_dir(app)?;
    let dir = base.join(VERSIONS_DIR);
    std::fs::create_dir_all(&dir).map_err(|e| format!("Cannot create versions dir: {e}"))?;

    let backup_size_mb = backup_path.and_then(|p| {
        std::fs::metadata(p).ok().map(|m| (m.len() as f64) / (1024.0 * 1024.0))
    });

    let meta = VersionMetadata {
        version: version.to_string(),
        installed_at: chrono::Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string(),
        path: exe_path.to_string_lossy().to_string(),
        previous_version: previous_version.map(String::from),
        backup_path: backup_path.map(|p| p.to_string_lossy().to_string()),
        backup_size_mb,
    };

    let path = current_json_path(app)?;
    let s = serde_json::to_string_pretty(&meta).map_err(|e| e.to_string())?;
    std::fs::write(&path, s).map_err(|e| e.to_string())?;
    Ok(())
}

/// Create backup of current executable before update. Returns path to backup.
pub fn backup_current_exe(app: &AppHandle, current_version: &str) -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| format!("Cannot find current binary: {e}"))?;
    let backup_dir = backups_dir(app)?;
    let name = format!("voiceforge-{}.AppImage", current_version);
    let backup_path = backup_dir.join(&name);

    let size = exe.metadata().map_err(|e| e.to_string())?.len();
    if size > MAX_BACKUP_MB * 1024 * 1024 {
        return Err(format!(
            "Current binary too large to backup ({} MB > {} MB limit)",
            size / (1024 * 1024),
            MAX_BACKUP_MB
        ));
    }

    std::fs::copy(&exe, &backup_path).map_err(|e| format!("Backup failed: {e}"))?;
    Ok(backup_path)
}
