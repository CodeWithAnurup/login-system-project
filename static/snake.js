// Nokia Snake (retro) - vanilla JS with sound effects
(() => {
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');

  // UI elements
  const speedRange = document.getElementById('speedRange');
  const speedValue = document.querySelector('.speed-value');
  const cellSizeRange = document.getElementById('cellSize');
  const cellValue = document.querySelector('.cell-value');
  const startBtn = document.getElementById('startBtn');
  const pauseBtn = document.getElementById('pauseBtn');
  const restartBtn = document.getElementById('restartBtn');
  const modal = document.getElementById('gameOverModal');
  const finalScore = document.getElementById('finalScore');
  const modalRestart = document.getElementById('modalRestart');
  const modalClose = document.getElementById('modalClose');

  // sound UI
  const soundToggle = document.getElementById('soundToggle');
  const volRange = document.getElementById('volRange');

  // Touch controls container
  const touchControls = document.getElementById('touchControls');

  // Game variables
  let grid = 20;
  let tickSpeed = 8;
  let cellPx = 24;
  let cols = 0, rows = 0;
  let snake = [];
  let dir = 'right';
  let nextDir = 'right';
  let food = null;
  let running = false;
  let timer = null;
  let score = 0;
  let paused = false;

  // AUDIO: preload and control
  const audio = {
    eat: new Audio('/static/sounds/eat.mp3'),
    gameover: new Audio('/static/sounds/gameover.mp3'),
    move: new Audio('/static/sounds/move.mp3'),
    bg: new Audio('/static/sounds/bgloop.mp3')
  };

  // Basic settings for audio objects
  Object.values(audio).forEach(a => {
    if (!a) return;
    a.preload = 'auto';
    a.loop = false;
    a.volume = parseFloat(volRange ? volRange.value : 0.8);
  });
  // background loop should loop if provided
  if (audio.bg) {
    audio.bg.loop = true;
    audio.bg.volume = 0.15;
  }

  let soundEnabled = true;

  function setVolume(v) {
    Object.values(audio).forEach(a => {
      if (!a) return;
      // keep bg quieter by default
      if (a === audio.bg) a.volume = Math.max(0, v * 0.25);
      else a.volume = v;
    });
  }

  // user toggles sound
  if (soundToggle) {
    soundToggle.addEventListener('click', () => {
      soundEnabled = !soundEnabled;
      soundToggle.textContent = soundEnabled ? '🔊 Sound' : '🔇 Muted';
      if (soundEnabled && audio.bg) {
        // play background on user gesture
        audio.bg.play().catch(()=>{ /* autoplay may be blocked until next gesture */ });
      } else {
        if (audio.bg) audio.bg.pause();
        // stop other sounds
        Object.values(audio).forEach(a => { try{ a.pause(); a.currentTime = 0; }catch{} });
      }
    });
  }

  if (volRange) {
    volRange.addEventListener('input', () => {
      const v = parseFloat(volRange.value);
      setVolume(v);
    });
  }

  function playSound(name) {
    try {
      if (!soundEnabled) return;
      const s = audio[name];
      if (!s) return;
      // clone for overlapping short effects (so multiple eats don't cut)
      const copy = s.cloneNode();
      copy.volume = s.volume;
      copy.play().catch(()=>{/* user gesture required */});
    } catch (e) { /* ignore */ }
  }

  // Responsive resize
  function resizeCanvas(){
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.floor(rect.width);
    canvas.height = Math.floor(rect.height);
    cols = grid;
    rows = Math.floor((canvas.height / canvas.width) * cols);
    if (rows < 10) rows = 10;
    cellPx = Math.floor(canvas.width / cols);
  }

  function resetGame(initial=true) {
    snake = [{x: Math.floor(cols/3), y: Math.floor(rows/2)}];
    dir = 'right';
    nextDir = 'right';
    spawnFood();
    score = 0;
    paused = false;
    if (timer) { clearInterval(timer); timer = null; }
    if (running && !initial) {
      startLoop();
    }
    draw();
  }

  function spawnFood(){
    let tries=0;
    while(true){
      const fx = Math.floor(Math.random()*cols);
      const fy = Math.floor(Math.random()*rows);
      if (!snake.some(s=>s.x===fx && s.y===fy)) {
        food = {x:fx,y:fy};
        break;
      }
      if (++tries>2000) break;
    }
  }

  function draw(){
    ctx.fillStyle = "#071202";
    ctx.fillRect(0,0,canvas.width,canvas.height);

    // subtle grid
    ctx.strokeStyle = `rgba(0,0,0,0.03)`;
    for (let i=0;i<=cols;i++){
      ctx.beginPath();
      ctx.moveTo(i*cellPx,0);
      ctx.lineTo(i*cellPx,rows*cellPx);
      ctx.stroke();
    }

    // food
    if (food) {
      ctx.fillStyle = "#ffd54a";
      ctx.fillRect(food.x*cellPx+2, food.y*cellPx+2, cellPx-4, cellPx-4);
    }

    // snake
    for (let i=0;i<snake.length;i++){
      const s = snake[i];
      const grad = ctx.createLinearGradient(s.x*cellPx, s.y*cellPx, (s.x+1)*cellPx, (s.y+1)*cellPx);
      grad.addColorStop(0, "#2b5a00");
      grad.addColorStop(1, "#6bff00");
      ctx.fillStyle = grad;
      ctx.fillRect(s.x*cellPx+1, s.y*cellPx+1, cellPx-2, cellPx-2);
      ctx.strokeStyle = "#0b2000";
      ctx.strokeRect(s.x*cellPx+1, s.y*cellPx+1, cellPx-2, cellPx-2);
    }

    ctx.fillStyle = "#bfe5a7";
    ctx.font = `${Math.max(12, cellPx - 6)}px monospace`;
    ctx.fillText(`Score: ${score}`, 8, Math.min(28, cellPx));
  }

  function step() {
    if (paused) return;
    const pd = nextDir;
    if ((dir === 'left' && pd === 'right') || (dir === 'right' && pd === 'left') ||
        (dir === 'up' && pd === 'down') || (dir === 'down' && pd === 'up')) {
      // ignore reverse
    } else {
      dir = pd;
    }

    let head = {...snake[0]};
    if (dir === 'left') head.x--;
    if (dir === 'right') head.x++;
    if (dir === 'up') head.y--;
    if (dir === 'down') head.y++;

    if (head.x < 0) head.x = cols - 1;
    if (head.x >= cols) head.x = 0;
    if (head.y < 0) head.y = rows - 1;
    if (head.y >= rows) head.y = 0;

    // collision
    if (snake.some(s => s.x === head.x && s.y === head.y)) {
      playSound('gameover');
      gameOver();
      return;
    }

    snake.unshift(head);

    if (food && head.x === food.x && head.y === food.y) {
      score++;
      playSound('eat');
      spawnFood();
    } else {
      snake.pop();
      // optional move sound (comment out if noisy)
      // playSound('move');
    }

    draw();
  }

  function startLoop() {
    if (timer) clearInterval(timer);
    const interval = Math.max(20, 300 - (tickSpeed * 12));
    timer = setInterval(step, interval);
    // play bg if allowed
    if (audio.bg && soundEnabled) {
      audio.bg.play().catch(()=>{/* blocked until gesture */});
    }
  }

  function gameOver() {
    running = false;
    if (timer) { clearInterval(timer); timer = null; }
    finalScore.textContent = `Score: ${score}`;
    modal.classList.remove('hidden');
    // stop background
    if (audio.bg) { audio.bg.pause(); audio.bg.currentTime = 0; }
  }

  // Input handling
  document.addEventListener('keydown', (e)=>{
    const k = e.key.toLowerCase();
    if (k === 'arrowleft' || k==='a') nextDir = 'left';
    if (k === 'arrowright' || k==='d') nextDir = 'right';
    if (k === 'arrowup' || k==='w') nextDir = 'up';
    if (k === 'arrowdown' || k==='s') nextDir = 'down';
    if (e.key === ' ' || e.key === 'Spacebar') {
      paused = !paused;
    }
  });

  // touch swipe
  let touchStartX=0, touchStartY=0;
  canvas.addEventListener('touchstart', e=>{
    const t = e.touches[0];
    touchStartX = t.clientX;
    touchStartY = t.clientY;
  }, {passive:false});
  canvas.addEventListener('touchend', e=>{
    const t = e.changedTouches[0];
    const dx = t.clientX - touchStartX;
    const dy = t.clientY - touchStartY;
    if (Math.abs(dx) > Math.abs(dy)) {
      if (dx > 20) nextDir = 'right';
      else if (dx < -20) nextDir = 'left';
    } else {
      if (dy > 20) nextDir = 'down';
      else if (dy < -20) nextDir = 'up';
    }
  }, {passive:false});

  // on-screen buttons
  document.querySelectorAll('.touch').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      nextDir = btn.dataset.dir;
    });
    btn.addEventListener('touchstart', e=>{
      e.preventDefault();
      nextDir = btn.dataset.dir;
    });
  });

  // UI events
  speedRange.addEventListener('input', ()=>{
    tickSpeed = parseInt(speedRange.value, 10);
    speedValue.textContent = tickSpeed;
    if (running) startLoop();
  });
  cellSizeRange.addEventListener('input', ()=>{
    grid = parseInt(cellSizeRange.value, 10);
    cellValue.textContent = grid;
    resizeCanvas();
    resetGame(false);
  });

  startBtn.addEventListener('click', ()=>{
    if (!running) {
      tickSpeed = parseInt(speedRange.value,10);
      grid = parseInt(cellSizeRange.value,10);
      resizeCanvas();
      running = true;
      resetGame(false);
      startLoop();
    } else {
      paused = false;
    }
  });

  pauseBtn.addEventListener('click', ()=>{
    paused = !paused;
    pauseBtn.textContent = paused ? 'Resume' : 'Pause';
  });

  restartBtn.addEventListener('click', ()=>{
    running = true;
    paused = false;
    resizeCanvas();
    resetGame(false);
    startLoop();
    modal.classList.add('hidden');
  });

  modalRestart.addEventListener('click', ()=>{
    modal.classList.add('hidden');
    running = true;
    paused = false;
    resizeCanvas();
    resetGame(false);
    startLoop();
  });
  modalClose.addEventListener('click', ()=>{
    modal.classList.add('hidden');
  });

  // window resize
  window.addEventListener('resize', ()=>{
    if (running) {
      resizeCanvas();
      draw();
    } else {
      resizeCanvas();
      draw();
    }
  });

  // initial UI
  function initUI(){
    speedValue.textContent = speedRange.value;
    cellValue.textContent = cellSizeRange.value;
    grid = parseInt(cellSizeRange.value,10);
    tickSpeed = parseInt(speedRange.value,10);
    resizeCanvas();
    resetGame(true);
    draw();
  }

  // add touchscreen controls dynamically for small screens
  if (!document.getElementById('touchControls') && window.innerWidth < 900) {
    const tc = document.createElement('div');
    tc.id = 'touchControls';
    tc.className = 'touch-controls';
    tc.innerHTML = '<button class="touch up" data-dir="up">▲</button><div style="display:flex;gap:8px"><button class="touch left" data-dir="left">◀</button><button class="touch down" data-dir="down">▼</button><button class="touch right" data-dir="right">▶</button></div>';
    document.querySelector('.snake-hero').appendChild(tc);
    tc.querySelectorAll('button').forEach(b=>{
      b.addEventListener('touchstart', e=>{e.preventDefault(); nextDir=b.dataset.dir});
      b.addEventListener('click', ()=> nextDir=b.dataset.dir);
    });
  }

  // ensure audio doesn't autoplay until user interacts:
  // play a silent sound on first user click to unlock audio in some browsers
  function unlockAudioOnUserInteraction() {
    const unlock = () => {
      // try to play then pause quickly to unlock
      Object.values(audio).forEach(a => {
        try {
          a.play().then(()=>{ a.pause(); a.currentTime = 0; }).catch(()=>{});
        } catch {}
      });
      window.removeEventListener('click', unlock);
      window.removeEventListener('keydown', unlock);
    };
    window.addEventListener('click', unlock, { once: true });
    window.addEventListener('keydown', unlock, { once: true });
  }
  unlockAudioOnUserInteraction();

  // init
  initUI();

})();
