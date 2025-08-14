document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.bg_test-img');
    let current = 0;
    let next = 1;

    // 最初の画像だけ表示
    images.forEach((img) => img.style.opacity = '0');
    images[current].style.opacity = '1';

    function crossFade() {
        images[next].style.opacity = '0.5'; // 次の画像を浮かせる

        setTimeout(() => {
            images[current].style.opacity = '0';
            images[next].style.opacity = '1';
            current = next;
            next = (next + 1) % images.length;
        }, 2000); // 2秒間重ねる

        setTimeout(crossFade, 7000);
    }

    setTimeout(crossFade, 7000);
});