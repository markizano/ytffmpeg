$(document).ready(function() {
  let videoInputCount = 1;

  // Add video input handler
  $('#add-video').on('click', function() {
    videoInputCount++;
    const videoInput = `
      <div class="video-input">
        <div class="form-group">
          <label>Video File ${videoInputCount}</label>
          <input type="file" name="video" accept="video/*" required>
        </div>
        <div class="form-group">
          <label>Override Filename (optional)</label>
          <input type="text" placeholder="custom-name.mp4">
        </div>
      </div>
    `;
    $('#video-inputs').append(videoInput);
  });

  // Form submission handler
  $('#upload-form').on('submit', function(e) {
    e.preventDefault();
    submitForm();
  });

  function submitForm() {
    const formData = new FormData();

    // Build project configuration matching schema.json
    const projectName = $('#project-name').val().trim();
    const title = $('#title').val().trim();
    const description = $('#description').val().trim();
    const baseLanguage = $('#language').val();
    const additionalLanguages = $('#additional-languages').val()
      .split(',')
      .map(lang => lang.trim())
      .filter(lang => lang.length > 0);
    const subtitles = $('#subtitles').is(':checked');
    const cutSilence = $('#cut-silence').is(':checked');
    const device = $('#device').val();

    // Build languages array (base + additional)
    const languages = [baseLanguage, ...additionalLanguages];

    // Project configuration
    const projectConfig = {
      ytffmpeg: {
        language: baseLanguage,
        languages: languages,
        subtitles: subtitles,
        cut_silence: cutSilence,
        device: device
      },
      videos: []
    };

    // Add metadata if provided
    const metadata = {};
    if (title) metadata.title = title;
    if (description) metadata.description = description;

    // Check if we have multiple videos (concatenation mode)
    const videoFiles = [];
    $('.video-input').each(function() {
      const fileInput = $(this).find('input[type="file"]')[0];
      const overrideName = $(this).find('input[type="text"]').val().trim();

      if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const fileName = overrideName || file.name;
        videoFiles.push({ file: file, name: fileName });
      }
    });

    if (videoFiles.length === 0) {
      showStatus('Please select at least one video file', 'error');
      return;
    }

    // For each video file, append to formData with its name
    videoFiles.forEach(function(videoFile) {
      formData.append('videos', videoFile.file, videoFile.name);
    });

    // Add project configuration
    formData.append('project_name', projectName);
    formData.append('project_config', JSON.stringify(projectConfig));
    if (Object.keys(metadata).length > 0) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    // Show progress container
    $('#progress-container').show();
    $('#submit-btn').prop('disabled', true);
    hideStatus();

    // AJAX upload with progress tracking
    $.ajax({
      url: '/api/process',
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      xhr: function() {
        const xhr = new window.XMLHttpRequest();
        xhr.upload.addEventListener('progress', function(e) {
          if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            updateProgress(percent);
          }
        }, false);
        return xhr;
      },
      success: function(response) {
        updateProgress(100);
        showStatus(
          'Upload successful! Your video is being processed. ' +
          'You will receive a notification when complete.',
          'success'
        );

        // Reset form after 3 seconds and redirect to projects
        setTimeout(function() {
          $('#upload-form')[0].reset();
          $('#submit-btn').prop('disabled', false);
          $('#progress-container').hide();
          window.location.href = '/videos';
        }, 3000);
      },
      error: function(xhr) {
        const errorMsg = xhr.responseJSON?.error || 'Upload failed. Please try again.';
        showStatus('Error: ' + errorMsg, 'error');
        $('#submit-btn').prop('disabled', false);
        $('#progress-container').hide();
      }
    });
  }

  function updateProgress(percent) {
    $('#progress-fill').css('width', percent + '%');
    $('#progress-text').text('Uploading: ' + percent + '%');
  }

  function showStatus(message, type) {
    const statusDiv = $('#status-message');
    statusDiv.text(message);
    statusDiv.removeClass('success error');
    statusDiv.addClass(type);
    statusDiv.show();
  }

  function hideStatus() {
    $('#status-message').hide();
  }
});
