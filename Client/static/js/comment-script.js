document.addEventListener('DOMContentLoaded', function () {    
    //image click, to fill out modal info with correct image info
        const imageModal = document.getElementById('imageModal');
        imageModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget; //get the one that was clicked on
            const imageId = button.getAttribute('data-id');
            const imageCaption = button.getAttribute('data-caption');
            const imageCategory = button.getAttribute('data-category');
            const imageSrc = button.getAttribute('src');

            //update everything based on one clicked
            const modalTitle = imageModal.querySelector('.modal-title');
            const modalImage = document.getElementById('modalImage');
            const modalCategory = document.getElementById('imageCategory');
            const imageIdField = document.getElementById('imageId');

            modalTitle.textContent = imageCaption;
            modalImage.src = imageSrc;
            modalCategory.textContent = imageCategory;
            imageIdField.value = imageId;

            //comments for the specific image id of the selected img 
            loadComments(imageId);
        });

        //for form submitting
        const commentForm = document.getElementById('commentForm');
        commentForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const imageId = document.getElementById('imageId').value;
            const commentText = document.getElementById('commentText').value;

            if (commentText.trim() === '') {
                alert('Please enter a comment.');
                return;
            }

            saveComment(imageId, commentText);
        });

        //load comments when clicking on image
        function loadComments(imageId) {
            const commentsList = document.getElementById('commentsList');
            commentsList.innerHTML = '<p>Loading comments...</p>';

            fetch(`/api/comments/${imageId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.comments && data.comments.length > 0) {
                        commentsList.innerHTML = '';
                        data.comments.forEach(comment => {
                            commentsList.innerHTML += `
                <div class="comment mb-2 p-2 border-bottom">
                  <p class="mb-1">${comment.text}</p>
                  <small class="text-muted">Posted on ${comment.timestamp}</small>
                </div>
              `;
                        });
                    } else {
                        commentsList.innerHTML = '<p>No comments yet.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error loading comments:', error);
                    commentsList.innerHTML = '<p>couldnt load comments.</p>';
                });
        }

        function saveComment(imageId, commentText) {
            fetch('/api/comments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    imageId: imageId,
                    text: commentText
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        //clear the comment box text and reload comments, so new one appears
                        document.getElementById('commentText').value = '';
                        loadComments(imageId);
                    } else {
                        alert('failed to save comment: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error saving comment:', error);
                    alert('error while saving your comment.');
                });
        }
});