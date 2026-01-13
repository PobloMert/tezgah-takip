# Installation Instructions for TezgahTakip v2.1.4

## System Requirements

- **Operating System**: Windows 7/8/10/11 (64-bit recommended)
- **Memory**: Minimum 2GB RAM
- **Storage**: 100MB free space
- **Network**: Internet connection for updates
- **Permissions**: Administrator rights (for installation)

## Installation Methods

### Method 1: Automatic Update (Recommended)

1. **Open Current TezgahTakip**
   - Launch TezgahTakip Launcher
   - Ensure internet connection is active

2. **Check for Updates**
   - Click "Güncelleme Kontrol" / "Update Check" button
   - Wait for update detection

3. **Install Update**
   - When v2.1.4 is detected, click "Yes" / "Evet"
   - Wait for automatic download and installation
   - Application will restart automatically

### Method 2: Manual Installation

1. **Download Release**
   - Visit: https://github.com/your-username/TezgahTakip/releases/tag/v2.1.4
   - Download: `TezgahTakip-v2.1.4-Windows.exe`

2. **Backup Current Installation**
   - Copy your current TezgahTakip folder to a safe location
   - This ensures you can rollback if needed

3. **Install New Version**
   - Close any running TezgahTakip instances
   - Run the downloaded installer
   - Follow installation prompts
   - Choose installation directory (or keep existing)

4. **Verify Installation**
   - Launch TezgahTakip
   - Check version in About dialog
   - Verify all features work correctly

### Method 3: Source Code Installation

1. **Download Source**
   - Download: `TezgahTakip-v2.1.4-Source.zip`
   - Extract to desired location

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**
   ```bash
   python launcher.py
   ```

## Post-Installation Verification

### Verify Update Success

1. **Check Version**
   - Open TezgahTakip
   - Version should show v2.1.4

2. **Test Core Functions**
   - Create a test entry
   - Verify database connectivity
   - Test backup/restore functions

3. **Verify Update System**
   - Check that enhanced update system is active
   - Verify automatic backup creation
   - Test error recovery mechanisms

### Troubleshooting

#### Issue: Update fails with permission error
**Solution**: 
- Run as Administrator
- Or move installation to user directory (C:\Users\[username]\TezgahTakip)

#### Issue: Antivirus blocks installation
**Solution**:
- Temporarily disable antivirus
- Add TezgahTakip to antivirus exceptions
- Re-enable antivirus after installation

#### Issue: Application won't start after update
**Solution**:
- Use automatic rollback feature
- Or restore from backup manually
- Or reinstall from scratch

## Rollback Instructions

If you need to rollback to previous version:

### Automatic Rollback
1. Launch TezgahTakip Launcher
2. If update failed, launcher will offer rollback options
3. Select "Restore from Backup"
4. Wait for automatic restoration

### Manual Rollback
1. Close TezgahTakip
2. Delete current installation folder
3. Restore from your manual backup
4. Launch TezgahTakip to verify

## Support

If you encounter any issues:

1. **Check Logs**: Look in `logs/` folder for error details
2. **Try Recovery**: Use built-in recovery options
3. **Report Issues**: Create issue on GitHub with log files
4. **Get Help**: Contact support through GitHub Issues

---

**Important**: Always backup your data before major updates!