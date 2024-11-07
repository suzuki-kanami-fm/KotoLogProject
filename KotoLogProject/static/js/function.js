$(document).ready(function() {
    // ボタンの表示・非表示を切り替える関数
    function toggleButtonVisibility($carouselTrack, $prevButton, $nextButton) {
        const $items = $carouselTrack.children('.carousel-item');
        const itemWidth = $items.outerWidth(true);
        const currentLeft = parseInt($carouselTrack.css('transform').split(',')[4]) || 0;
        const trackWidth = $carouselTrack.width();
        const maxScroll = trackWidth - $items.length * itemWidth;

        // カードが1枚しかない場合、または、すべてのカードが画面内に収まっている場合、両方のボタンを非表示にする
        if (($items.length <= 1)|| ($items.length * itemWidth <= trackWidth)) {
            $prevButton.hide();
            $nextButton.hide();
            return;  // ここで終了して、他の条件はチェックしない
        }
        
        // 1枚目が見えているときは左ボタンを非表示、それ以外は表示
        if (currentLeft >= 0) {
            $prevButton.hide();
        } else {
            $prevButton.show();
        }

        // 最後のカードが見えているときは右ボタンを非表示、それ以外は表示
        if (Math.abs(currentLeft) >= Math.abs(maxScroll)) {
            $nextButton.hide();
        } else {
            $nextButton.show();
        }
    }

    function moveCarousel(target, direction) {
        const $carouselTrack = $(target).find('.carousel-track');
        const $prevButton = $(target).find('.carousel-prev');
        const $nextButton = $(target).find('.carousel-next');
        const $items = $carouselTrack.children('.carousel-item');
        const itemWidth = $items.outerWidth(true);
        let currentLeft = parseInt($carouselTrack.css('transform').split(',')[4]) || 0;
        const trackWidth = $carouselTrack.width();
        const maxScroll = trackWidth - $items.length * itemWidth;

        if (direction === 'next') {
            if (Math.abs(currentLeft) < Math.abs(maxScroll)) {
                currentLeft -= itemWidth;
                $carouselTrack.css('transform', `translateX(${currentLeft}px)`);
            }
        } else if (direction === 'prev') {
            if (currentLeft < 0) {
                currentLeft += itemWidth;
                $carouselTrack.css('transform', `translateX(${currentLeft}px)`);
            }
        }

        // ボタンの表示・非表示を更新
        setTimeout(() => toggleButtonVisibility($carouselTrack, $prevButton, $nextButton), 450);
    }

    // ボタンのクリックイベント
    $('.carousel-prev').click(function() {
        const target = $(this).data('target');
        moveCarousel(target, 'prev');
    });

    $('.carousel-next').click(function() {
        const target = $(this).data('target');
        moveCarousel(target, 'next');
    });

    // 初期表示で各カルーセルのボタン状態を更新
    $('.carousel-container').each(function() {
        const $carouselTrack = $(this).find('.carousel-track');
        const $prevButton = $(this).find('.carousel-prev');
        const $nextButton = $(this).find('.carousel-next');
        toggleButtonVisibility($carouselTrack, $prevButton, $nextButton);
    });

    // 画面幅変更時にボタンの表示・非表示を再確認
    $(window).resize(function() {
        $('.carousel-container').each(function() {
            const $carouselTrack = $(this).find('.carousel-track');
            const $prevButton = $(this).find('.carousel-prev');
            const $nextButton = $(this).find('.carousel-next');
            toggleButtonVisibility($carouselTrack, $prevButton, $nextButton);
        });
    });
});
