/* 다정이 그래픽 (인라인 SVG). 사람을 그리지 않고 도형·기기·말풍선 조합으로만 표현한다. 라임 / 검정 / 흰색 3색. */
(function () {
  const K = "#111111", L = "#FFE59A", W = "#FFFDFA", G = "#F4F0EA";

  const st = document.createElement('style'); st.textContent = '@keyframes blink{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}.blink{animation:blink 5s infinite;transform-box:fill-box;transform-origin:center}@media (prefers-reduced-motion:reduce){.blink{animation:none}}'; document.head.appendChild(st);
  window.ILLUS = {
    // 히어로: 거실 태블릿 + 말풍선 두 개 (라임 카드 위에 놓인다)
    grandma: `<svg viewBox='0 0 360 300' role='img' aria-label='태블릿 위의 대화'>
      <path d='M20 150 A110 110 0 0 1 130 40 L130 150 Z' fill='${K}'/>
      <circle cx='300' cy='60' r='34' fill='${W}'/>
      <circle cx='60' cy='250' r='12' fill='${K}'/>
      <g transform='rotate(-6 190 170)'>
        <rect x='80' y='95' width='230' height='160' rx='22' fill='${K}'/>
        <rect x='92' y='107' width='206' height='136' rx='14' fill='${G}'/>
        <rect x='106' y='124' width='112' height='36' rx='14' fill='${K}'/>
        <rect x='120' y='139' width='54' height='6' rx='3' fill='${L}'/><rect x='182' y='139' width='22' height='6' rx='3' fill='${L}'/>
        <rect x='150' y='170' width='134' height='36' rx='14' fill='${L}'/>
        <circle cx='172' cy='188' r='4' fill='${K}'/><circle cx='188' cy='188' r='4' fill='${K}'/><circle cx='204' cy='188' r='4' fill='${K}'/>
        <rect x='106' y='214' width='60' height='14' rx='7' fill='${W}'/>
        <circle cx='195' cy='251' r='3' fill='${G}'/>
      </g>
    </svg>`,

    // 신청 섹션: 휴대폰 + 주간 막대 + 상태 배지 (검정 카드 위)
    child: `<svg viewBox='0 0 300 260' role='img' aria-label='보호자 앱 리포트'>
      <circle cx='230' cy='70' r='52' fill='${L}'/>
      <path d='M40 240 A70 70 0 0 1 110 170 L110 240 Z' fill='${L}'/>
      <rect x='96' y='28' width='140' height='220' rx='26' fill='${W}'/>
      <rect x='110' y='44' width='112' height='34' rx='12' fill='${K}'/>
      <rect x='122' y='58' width='52' height='6' rx='3' fill='${L}'/>
      <rect x='112' y='92' width='24' height='54' rx='6' fill='${L}'/><rect x='142' y='104' width='24' height='42' rx='6' fill='${L}'/><rect x='172' y='84' width='24' height='62' rx='6' fill='${K}'/><rect x='202' y='110' width='20' height='36' rx='6' fill='${L}'/>
      <rect x='112' y='160' width='110' height='26' rx='13' fill='${G}'/><circle cx='128' cy='173' r='5' fill='#5BBE8E'/><rect x='140' y='170' width='60' height='6' rx='3' fill='${K}'/>
      <rect x='112' y='196' width='110' height='26' rx='13' fill='${G}'/><circle cx='128' cy='209' r='5' fill='#F2B33D'/><rect x='140' y='206' width='44' height='6' rx='3' fill='${K}'/>
    </svg>`,

    // 말풍선 두 개
    bubbles: `<svg viewBox='0 0 240 160' role='img' aria-label='대화'>
      <path d='M24 28 h120 a18 18 0 0 1 18 18 v36 a18 18 0 0 1 -18 18 h-70 l-28 22 v-22 h-22 a18 18 0 0 1 -18 -18 v-36 a18 18 0 0 1 18 -18z' fill='${K}'/>
      <rect x='44' y='54' width='64' height='8' rx='4' fill='${L}'/><rect x='44' y='70' width='40' height='8' rx='4' fill='${L}'/>
      <path d='M100 60 h118 a18 18 0 0 1 18 18 v36 a18 18 0 0 1 -18 18 h-20 v22 l-28 -22 h-70 a18 18 0 0 1 -18 -18 v-36 a18 18 0 0 1 18 -18z' fill='${L}'/>
      <circle cx='140' cy='96' r='5' fill='${K}'/><circle cx='158' cy='96' r='5' fill='${K}'/><circle cx='176' cy='96' r='5' fill='${K}'/>
    </svg>`,

    // 막대 + 선 그래프
    chart: `<svg viewBox='0 0 240 160' role='img' aria-label='변화 그래프'>
      <rect x='24' y='20' width='192' height='120' rx='20' fill='${W}'/>
      <rect x='48' y='92' width='20' height='32' rx='6' fill='${L}'/><rect x='80' y='72' width='20' height='52' rx='6' fill='${L}'/><rect x='112' y='84' width='20' height='40' rx='6' fill='${K}'/><rect x='144' y='56' width='20' height='68' rx='6' fill='${L}'/><rect x='176' y='66' width='20' height='58' rx='6' fill='${L}'/>
      <path d='M58 78 L90 60 L122 70 L154 42 L186 50' fill='none' stroke='${K}' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/><circle cx='154' cy='42' r='6' fill='${K}'/>
    </svg>`,

    // 집 + 하트
    home: `<svg viewBox='0 0 240 160' role='img' aria-label='가족'>
      <path d='M60 76 L120 30 L180 76 V128 a12 12 0 0 1 -12 12 H72 a12 12 0 0 1 -12 -12 Z' fill='${L}'/>
      <rect x='104' y='96' width='32' height='44' rx='6' fill='${K}'/>
      <path d='M120 72 c-6 -12 -24 -8 -22 6 c1 9 12 14 22 24 c10 -10 21 -15 22 -24 c2 -14 -16 -18 -22 -6z' fill='${W}'/>
    </svg>`,

    // 태블릿 아바타: 다정이 마크 (검정 원 + 라임 점)
    avatar: `<svg viewBox='0 0 100 86' role='img' aria-label='다정이'><path class='blob' d='M48 4c26-2 48 12 48 40s-18 40-46 40S2 70 4 42 22 6 48 4z' fill='${L}'/><g class='blink'><ellipse cx='54' cy='36' rx='5' ry='7' fill='${K}'/><ellipse cx='68' cy='37' rx='5' ry='7' fill='${K}'/></g></svg>`,

    mark: `<svg viewBox='0 0 120 100' role='img' aria-label='다정이'><path d='M58 6c30-4 56 14 58 44s-20 46-54 48S4 86 4 54 28 10 58 6z' fill='${K}'/><g class='blink'><ellipse cx='64' cy='44' rx='8' ry='11' fill='${W}'/><ellipse cx='88' cy='46' rx='8' ry='11' fill='${W}'/></g></svg>`,
  };
})();
