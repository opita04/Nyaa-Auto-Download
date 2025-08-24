# Warp Terminal Rules for Nyaa Auto Download Project

## Project Context Management Rules
- **Always maintain project context files**: Keep `/cursor-docs/CHANGELOG.md`, `/cursor-docs/ARCHITECTURE.md`, and `/cursor-docs/CURSOR-CONTEXT.md` updated
- **Pattern**: `.*` (applies to all files)
- **Instructions**:
  - Whenever you create, edit, or suggest code, also update `/cursor-docs/CHANGELOG.md` with a dated summary of the changes. Include file paths and the reason for the change.
  - If any new folder, component, or major refactor is introduced, update `/cursor-docs/ARCHITECTURE.md` to reflect the current structure of the project. Include directory maps, key components, and their purpose.
  - Keep `/cursor-docs/CURSOR-CONTEXT.md` as a short, living summary of current features, in-progress work, dependencies, and known issues. Update this whenever features are added, modified, or removed.
  - Before suggesting or making changes, always review `/cursor-docs/CURSOR-CONTEXT.md` and `/cursor-docs/ARCHITECTURE.md` to stay aligned with the project structure and goals.

## LOGGING GUIDELINES
- **Targeted Logging Only**: Add logging only at critical points where debugging is needed
- **Maximum 3-5 logs per function**: Don't spam the console with excessive logging
- **Log only when necessary**:
  - Function entry/exit for complex functions
  - Error conditions and fallbacks
  - State changes that affect user experience
  - API call results (success/failure only)
- **Remove debug logs after fixing issues**: Don't leave excessive logging in production code
- **Use meaningful log messages**: Include relevant data, not just "function called"
- **Input Validation**: Validate all Cloud Function inputs
- **Rate Limiting**: Implement appropriate rate limiting
- **Error Messages**: Don't expose sensitive information in error responses
- **API Key Management**: Use environment variables for sensitive keys

## DEVELOPMENT WORKFLOW

### Before Making Changes
1. Check current task status and requirements
2. Research relevant documentation and examples
3. Plan implementation approach
4. Consider impact on existing functionality
5. Verify Firebase SDK version compatibility
6. Plan AI integration strategy and fallbacks

### After Making Changes
- **Always rebuild the executable**: After modifying code or building new features, immediately rebuild the exe using the build commands
- **Execute the rebuild**: Use the most reliable build method based on lessons learned:
  1. **Primary method**: `pyinstaller "NyaDownloader.spec"` (direct PyInstaller with correct spec)
  2. **Fallback**: `python build_exe.py` (may use wrong spec file priority)
  3. **Last resort**: `.\rebuild_exe.bat` (often fails due to spec file issues)
- **Test the rebuilt exe**: Verify that the new executable works correctly with the implemented changes
- **Verify build success**: Check that `dist/NyaDownloader.exe` exists and has reasonable file size (~18-19 MB)

## EXECUTABLE BUILD LESSONS LEARNED
- **Spec File Priority**: The project now uses `"NyaDownloader.spec"` for the executable build
- **Build Script Issues**: The `build_exe.py` script checks spec files in wrong order, prioritizing the incorrect one
- **Batch Script Problems**: The `rebuild_exe.bat` often fails due to spec file selection issues
- **Direct PyInstaller**: Most reliable method is direct PyInstaller command with correct spec file
- **Build Verification**: Always check file size (~18.8 MB) and test basic functionality (headless mode)
- **Common Failures**: 
  - "Build successful!" followed by "Build failed!" indicates spec file or path issues
  - Missing executable in dist/ folder means build actually failed despite success messages
- **PowerShell Syntax**: Use `& "path\to\exe.exe"` syntax for running executables with spaces in names

## WARP-SPECIFIC GUIDELINES
- **Terminal Commands**: When suggesting commands, ensure they work in PowerShell (pwsh) environment
- **File Paths**: Use Windows-style paths with backslashes when appropriate
- **Environment Variables**: Reference Windows environment variable syntax when needed
- **Project Structure**: Maintain awareness of the Nyaa Auto Download project structure and dependencies
- **Firebase Integration**: Consider Firebase deployment and configuration when making suggestions
- **GitHub Integration**: Remember to suggest Git operations for version control when appropriate
