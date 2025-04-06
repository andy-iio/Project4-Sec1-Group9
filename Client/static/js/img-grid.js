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