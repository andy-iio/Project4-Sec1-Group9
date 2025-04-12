// home-filter.js -category filtering for home page and vault page

document.addEventListener('DOMContentLoaded', function() {
   
    const filterButtons = document.querySelectorAll('[data-filter]');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.getAttribute('data-filter');
            
            
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            
            this.classList.add('active');
            
            if (category === 'all') {
                showAllPosts();
            } else {
                filterByCategory(category);
            }
        });
    });
});

/**
 * Show posts from a specific category
 */
function filterByCategory(category) {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        const cardCategory = card.querySelector('.card-text').textContent;
        if (cardCategory === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
    

    relayoutMasonry();
}
/* Show all posts*/
function showAllPosts() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.display = 'block';
    });
    
    // Re-layout masonry
    relayoutMasonry();
}

/**
 * Re-layout masonry grid
 */
function relayoutMasonry() {
    const grid = document.querySelector('#masonry-grid');
    if (grid) {
       
        setTimeout(() => {
            const msnry = new Masonry(grid);
            msnry.layout();
        }, 100);
    }
}