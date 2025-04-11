document.addEventListener('DOMContentLoaded', function () {
    //masonry info: https://masonry.desandro.com/
    //to make a grid, pinterest style
    var grid = document.querySelector('#masonry-grid');
    var masonry = new Masonry(grid, {
        itemSelector: '.card',
        columnWidth: '.card',
        percentPosition: true,
        gutter: 15
    });

    //layout after loading images
    var imgLoad = imagesLoaded(grid);
    imgLoad.on('progress', function () {
        masonry.layout();
    });
});

//when clicking the save image button on a specific image
document.addEventListener("DOMContentLoaded", function() {
    const saveButtons = document.querySelectorAll(".save-btn");

    saveButtons.forEach(button => {
        button.addEventListener("click", function() {
            const imageId = this.getAttribute("data-id");

            fetch('/save_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image_id: imageId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Image saved to your vault!!');
                } else {
                    alert('Couldnt save the image, please try again later.' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Couldnt save the image, please try again later.');
            });
        });
    });
});

