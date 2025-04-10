document.addEventListener('DOMContentLoaded', function () {
    const uploadButton = document.getElementById('upload-button');
    const uploadModal = document.getElementById('uploadModal');
    const closeBtn = uploadModal.querySelector('.btn-close');
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('image-preview');

    //open the modal on click
    uploadButton.addEventListener('click', function () {
        uploadModal.classList.add('show');
        uploadModal.style.display = 'block';
        document.body.classList.add('modal-open');

        //darken the background with a backdrop to make the modal easier to see
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        document.body.appendChild(backdrop);
    });

    function closeModal() {
        uploadModal.classList.remove('show');
        uploadModal.style.display = 'none';
        document.body.classList.remove('modal-open');

        //take away the backdrop on close
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }

    //close when clicking exit button
    closeBtn.addEventListener('click', closeModal);

    //close when clicking somewhere else 
    uploadModal.addEventListener('click', function (event) {
        if (event.target === uploadModal) {
            closeModal();
        }
    });

    //for img preview when file is selected
    imageInput.addEventListener('change', function () {
        if (this.files && this.files[0]) {
            const reader = new FileReader();

            reader.onload = function (e) {
                imagePreview.innerHTML = `<img src="${e.target.result}" class="img-fluid">`;
            }

            reader.readAsDataURL(this.files[0]);
        }
    });
});