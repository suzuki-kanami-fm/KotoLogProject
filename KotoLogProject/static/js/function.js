$(document).ready(function() {
    function moveCarousel(target, direction) {
        const $carouselTrack = $(target).find('.carousel-track');
        const $items = $carouselTrack.children('.carousel-item');
        const itemWidth = $items.outerWidth(true);
        let currentLeft = parseInt($carouselTrack.css('transform').split(',')[4]) || 0;
        const trackWidth = $carouselTrack.width();
        const maxScroll = trackWidth - $items.length * itemWidth;

        if (direction === 'next') {
            if (Math.abs(currentLeft) < Math.abs(maxScroll)) {
                $carouselTrack.css('transform', `translateX(${currentLeft - itemWidth}px)`);
            }
        } else if (direction === 'prev') {
            if (currentLeft < 0) {
                $carouselTrack.css('transform', `translateX(${currentLeft + itemWidth}px)`);
            }
        }
    }

    $('.carousel-prev').click(function() {
        const target = $(this).data('target');
        moveCarousel(target, 'prev');
    });

    $('.carousel-next').click(function() {
        const target = $(this).data('target');
        moveCarousel(target, 'next');
    });
});
