# ytffmpeg Web Interface

The ytffmpeg web interface provides a browser-based UI for uploading videos and managing video processing projects.

## Quick Start

### Start the Web Server

```bash
# Basic usage (default port 9091, workspace: ~/ytffmpeg-projects)
ytffmpeg serve

# Custom port and workspace
ytffmpeg serve --http-port 8080 --workspace /path/to/projects

# Custom webroot (for development)
ytffmpeg serve --webroot /path/to/web/assets
```

### Access the Interface

Once the server is running, open your browser to:
- **Main page**: http://localhost:9091/
- **Projects list**: http://localhost:9091/videos

## Features

### 1. Video Upload Form (`/`)

Upload and configure videos for processing:

#### Project Details
- **Project Name**: Unique identifier for your project (required)
- **Video Title**: Title metadata for the final video
- **Description**: Description metadata for the final video

#### Video Files
- Upload one or more video files
- For multiple videos, they will be concatenated automatically
- Override filenames if needed

#### Processing Options
- **Generate Subtitles**: Enable/disable subtitle generation (uses Whisper)
- **Base Language**: Language for subtitle transcription
- **Additional Languages**: Comma-separated list of languages for translation
- **Remove Silence**: Enable silence detection and removal
- **Processing Device**: Choose CPU, CUDA (GPU), or auto-detect

### 2. Projects List (`/videos`)

View all your video projects:
- Project names
- Last modified date
- Processing status (Unknown, Configured, Completed)
- Click "View Details" to see project information

### 3. Project Detail (`/video?project=<name>`)

View detailed information about a specific project:
- Project configuration (YAML)
- List of project files
- Output video player (when available)

## API Endpoints

The web interface exposes a REST API for programmatic access:

### GET /api/projects

Returns list of all projects in the workspace.

**Response:**
```json
{
  "projects": [
    {
      "name": "my-project",
      "modified": 1234567890.0,
      "status": "Completed"
    }
  ]
}
```

### GET /api/project/<project_name>

Returns detailed information about a specific project.

**Response:**
```json
{
  "name": "my-project",
  "config": { ... },
  "files": ["resources/video.mp4", "build/video.mkv"],
  "output_video": "output.mp4",
  "modified": 1234567890.0,
  "status": "Completed"
}
```

### POST /api/process

Upload videos and start processing pipeline.

**Request (multipart/form-data):**
- `project_name`: Project identifier (required)
- `project_config`: JSON configuration object
- `metadata`: JSON metadata object
- `videos`: One or more video files

**Response:**
```json
{
  "status": "success",
  "message": "Video upload successful. Processing started in background.",
  "project": "my-project"
}
```

## Configuration

The web server can be configured via:

1. **Command-line arguments**:
   ```bash
   ytffmpeg serve --workspace /path/to/projects --http-port 8080
   ```

2. **Environment variables**:
   ```bash
   export HTTP_PORT=8080
   ytffmpeg serve
   ```

3. **Configuration files** (`~/.config/ytffmpeg/config.yml`):
   ```yaml
   ytffmpeg:
     workspace: /path/to/projects
     http_port: 8080
     webroot: /custom/web/assets
   ```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `workspace` | `~/ytffmpeg-projects` | Directory where project folders are created |
| `http_port` | `9091` | TCP port for the web server |
| `webroot` | Auto-detected | Directory containing HTML/CSS/JS assets |

## Background Processing

When you upload a video:

1. **Upload**: Files are uploaded to a temporary directory
2. **Immediate Response**: Server returns 200 OK immediately
3. **Background Processing**: A background thread runs the ytffmpeg pipeline:
   - Creates project structure (`ytffmpeg new`)
   - Moves files to resources directory
   - Generates subtitles (`ytffmpeg refresh`)
   - Builds final video (`ytffmpeg build`)
4. **Notifications**: SNS notifications are sent on completion or failure

## File Organization

Each project has this structure:
```
workspace/
└── project-name/
    ├── build/                    # Generated files
    │   ├── video.mkv            # Converted video
    │   ├── video.en.srt         # Subtitles (base language)
    │   ├── video.es.srt         # Translated subtitles
    │   └── output.mp4           # Final output
    ├── resources/                # Uploaded files
    │   └── video.mp4
    ├── ytffmpeg.yml              # Project configuration
    └── readme.md
```

## Security Considerations

**WARNING**: The web interface is intended for trusted environments only:

- No authentication/authorization implemented
- Accepts large file uploads (up to 5GB)
- Executes video processing commands
- Binds to 0.0.0.0 (all interfaces)

**Recommendations for production:**
- Run behind a reverse proxy (nginx, Apache)
- Add authentication middleware
- Limit access via firewall rules
- Use HTTPS for encrypted connections
- Set up rate limiting

## Troubleshooting

### Server won't start

**Error**: `Webroot directory not found`
- Ensure web assets are installed: `pip install -e .`
- Or specify custom webroot: `--webroot /path/to/web`

**Error**: `Port already in use`
- Choose a different port: `--http-port 9092`
- Or kill the process using the port

### Upload fails

**Error**: `File too large`
- Default limit is 5GB per request
- Check CherryPy `server.max_request_body_size` setting

**Error**: `Project already exists`
- Choose a unique project name
- Or manually delete the existing project directory

### Processing fails

Check the server logs for detailed error messages. Common issues:
- Missing dependencies (whisper, ffmpeg)
- Insufficient disk space
- GPU memory exhaustion (try CPU mode)
- Corrupt video files

## Development

### Running in Development Mode

```bash
# Run directly from source
python lib/ytffmpeg/webserv.py

# Or use the CLI
ytffmpeg serve --log-level DEBUG
```

### Frontend Development

Frontend assets are in `web/`:
- `index.html` - Upload form
- `projects.html` - Projects list
- `project-detail.html` - Project detail view
- `style.css` - Shared styles
- `app.js` - JavaScript logic

Make changes to these files and refresh your browser.

### Future Enhancements

Planned features:
- Angular frontend for richer UI
- WebSocket support for real-time progress updates
- Project deletion/editing
- Batch processing
- Video preview/trimming tools
- Authentication and user management

## Examples

### Basic Upload

```bash
# Start server
ytffmpeg serve

# In browser: http://localhost:9091
# - Enter project name: "my-first-video"
# - Upload video file
# - Click "Upload and Process"
# - Wait for notification or check /videos page
```

### Multiple Videos (Concatenation)

```bash
# In browser:
# - Enter project name: "concatenated-video"
# - Upload first video
# - Click "+ Add Another Video"
# - Upload second video
# - Enable subtitles, select language
# - Click "Upload and Process"
```

### Custom Configuration

```bash
# Start with custom settings
ytffmpeg serve \
  --workspace /media/videos/projects \
  --http-port 8080 \
  --log-level DEBUG

# Access at http://localhost:8080
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/markizano/ytffmpeg/issues
- Documentation: https://ytffmpeg.markizano.net
- CLI Help: `ytffmpeg --help`
