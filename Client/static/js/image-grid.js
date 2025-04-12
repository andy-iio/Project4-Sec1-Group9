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
    // Handle Save to Vault buttons
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
                    
                    // Change button to Remove from Vault
                    this.textContent = 'Remove from Vault';
                    this.classList.remove('btn-success', 'save-btn');
                    this.classList.add('btn-danger', 'unsave-btn');
                    this.setAttribute('data-id', imageId);
                    
                    this.removeEventListener('click', arguments.callee);
                    
                    
                    this.addEventListener('click', handleUnsaveClick);
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
    
    //Remove from Vault buttons
    const unsaveButtons = document.querySelectorAll(".unsave-btn");
    unsaveButtons.forEach(button => {
        button.addEventListener("click", handleUnsaveClick);
    });
    
    // Function to handle unsave clicks
    function handleUnsaveClick() {
        const imageId = this.getAttribute("data-id");
        const currentPage = window.location.pathname;
        
        fetch('/unsave_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_id: imageId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Image removed from your saved posts');
                
                if (currentPage.includes('/saved')) {
                    // If on saved page, remove the card
                    const card = this.closest('.card');
                    if (card) {
                        card.remove();
                        
                        // Reapply masonry
                        var grid = document.querySelector('#masonry-grid');
                        if (grid) {
                            var masonry = new Masonry(grid, {
                                itemSelector: '.card',
                                columnWidth: '.card',
                                percentPosition: true,
                                gutter: 15
                            });
                            masonry.layout();
                        }
                        
                        // Check if grid is now empty
                        const remainingCards = document.querySelectorAll('#masonry-grid .card');
                        if (remainingCards.length === 0) {
                            const container = document.querySelector('.container.mt-4');
                            if (container) {
                                container.innerHTML = `
                                    <h1>Your Saved Posts:</h1>
                                    <div class="alert alert-info">
                                        <p>You haven't saved any posts yet. Go to the <a href="/">home page</a> to find and save posts!</p>
                                    </div>
                                `;
                            }
                        }
                    }
                } else {
                    // Otherwise, change button back to Save to Vault
                    this.textContent = 'Save to Vault';
                    this.classList.remove('btn-danger', 'unsave-btn');
                    this.classList.add('btn-success', 'save-btn');
                    this.setAttribute('data-id', imageId);
                    
                    this.removeEventListener('click', handleUnsaveClick);
                    
                    
                    this.addEventListener('click', function() {
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
                                
                                // Change button to Remove from Vault
                                this.textContent = 'Remove from Vault';
                                this.classList.remove('btn-success', 'save-btn');
                                this.classList.add('btn-danger', 'unsave-btn');
                                
                                this.removeEventListener('click', arguments.callee);
                                
                                this.addEventListener('click', handleUnsaveClick);
                            } else {
                                alert('Couldnt save the image, please try again later.' + data.message);
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Couldnt save the image, please try again later.');
                        });
                    });
                }
            } else {
                alert('Couldnt remove the image, please try again later.' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Couldnt remove the image, please try again later.');
        });
    }
});