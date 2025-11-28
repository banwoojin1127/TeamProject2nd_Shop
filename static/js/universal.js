// 페이지 최상단 이동용 버블 버튼 스크립트
$(document).ready(function(){
    // jQuery의 ready 이벤트는 DOM 로드가 완료된 후 실행됨을 보장합니다.
    const $popBtn = $("#pop.top-btn"); 
    
    $popBtn.click(function(){
        $('html, body').animate({scrollTop: 0}, 100);
        return false;
    });
});


