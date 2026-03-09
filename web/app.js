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
    try {
      const formData = new FormData();

      // Build project configuration matching schema.json
      const projectName = $('#project-name').val().trim();
      const title = $('#title').val().trim();
      const description = $('#description').val().trim();
      const subtitles = $('#subtitles').is(':checked');
      const cutSilence = $('#cut-silence').is(':checked');

      const videos = [];
      const videoData = {
        input: [],
        metadata: {
          title: title ?? '',
          description: description ?? '',
        }
      };

      const inputVideos = $('.video-input').map(function() {
        const fileInput = $(this).find('input[type="file"]')[0];
        const overrideName = $(this).find('input[type="text"]').val().trim();

        if (fileInput.files.length > 0) {
          const file = fileInput.files[0];
          const filename = overrideName || file.name;
          console.debug('Video Data', JSON.stringify(videoData,0,2));
          formData.append('videos', file, filename);
          return {video: file, filename};
        }
      }).get();
      console.log('Input Videos: ', inputVideos);
      if (inputVideos.length === 0) {
        // No videos == error.
        showStatus('Please select at least one video file', 'error');
        return;
      } else if (inputVideos.length === 1) {
        // Just submit the video.
        console.log('Single video upload.');
        videoData.input.push({i: inputVideos[0].filename});
        videoData.output = `build/${projectName}.mp4`;
      } else if (inputVideos.length > 1) {
        console.log('Multi-video upload for concat.');
        // Build the filter complex to combine the videos.
        const filterComplex = inputVideos.map((v, i) => `[${i}:v][${i}:a]`).join('') + `concat=n=${inputVideos.length}:a=1[video][audio]`
        const concatVideo = `resources/${projectName}_concat.mkv`;
        videos.push({
          input: inputVideos.map(v => ({i: v.filename})),
          output: concatVideo,
          filter_complex: [filterComplex]
        });
        videoData.input.push({i: concatVideo})
        videoData.output = `build/${projectName}.mp4`;
      }
      videos.push(videoData);

      // Project configuration
      const projectConfig = {
        ytffmpeg: {
          subtitles: subtitles,
          cut_silence: cutSilence,
        },
        videos: videos,
      };
      console.log('Project config payload: ', projectConfig);

      // Add project configuration
      formData.append('project_name', projectName);
      formData.append('project_config', JSON.stringify(projectConfig));

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
            // $('#upload-form')[0].reset();
            $('#submit-btn').prop('disabled', false);
            $('#progress-container').hide();
            // window.location.href = '/videos';
          }, 3000);
        },
        error: function(xhr) {
          console.log(xhr);
          let errorMsg;
          if (xhr.responseJSON.error) {
            errorMsg = xhr.responseJSON.error;
          } else if (xhr.response.error) {
            errorMsg = xhr.response.error;
          } else {
            errorMsg = 'Upload failed. Please try again.';
          }
          showStatus('Error: ' + errorMsg, 'error');
          $('#submit-btn').prop('disabled', false);
          $('#progress-container').hide();
        }
      });

    } catch (e) {
      showStatus(`Cannot process form: ${e}`, 'error');
    }
  }

  function updateProgress(percent) {
    $('#progress-fill').css('width', percent + '%');
    $('#progress-text').text('Uploading: ' + percent + '%');
    const position = $('#progress-container').offset();
    window.scrollTo(position.left, position.top)
  }

  function showStatus(message, type) {
    const statusDiv = $('#status-message');
    statusDiv.text(message);
    statusDiv.removeClass('success error');
    statusDiv.addClass(type);
    statusDiv.show();
    const position = statusDiv.offset();
    window.scrollTo(position.left, position.top)
  }

  function hideStatus() {
    $('#status-message').hide();
  }
});
