<script lang="ts">
  import { onMount } from 'svelte';

  export let wsUrl = 'ws://localhost:8766';
  export let centerHz = 156_800_000;
  export let bandwidthHz = 2_000_000;
  export let plotHeight = 260;

  let canvasEl: HTMLCanvasElement;
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectAttempts = 0;
  let connected = false;
  let sourceMode = 'disconnected';
  let frameRateHz = 20;
  let leftHz = centerHz - bandwidthHz / 2;
  let rightHz = centerHz + bandwidthHz / 2;
  let visibleSeconds = Math.max(1, Math.round(plotHeight / frameRateHz));

  function formatMHz(hz: number): string {
    return `${(hz / 1_000_000).toFixed(3)} MHz`;
  }

  function setCanvasSize() {
    if (!canvasEl) return;
    const dpr = window.devicePixelRatio || 1;
    const width = canvasEl.clientWidth;
    const height = plotHeight;

    canvasEl.width = Math.max(1, Math.floor(width * dpr));
    canvasEl.height = Math.max(1, Math.floor(height * dpr));

    const ctx = canvasEl.getContext('2d');
    if (!ctx) return;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    ctx.fillStyle = '#071126';
    ctx.fillRect(0, 0, width, height);
  }

  function colorForDbfs(dbfs: number): string {
    const t = Math.max(0, Math.min(1, (dbfs + 120) / 80));

    if (t < 0.25) {
      const p = t / 0.25;
      const r = Math.round(6 + 12 * p);
      const g = Math.round(24 + 96 * p);
      const b = Math.round(80 + 140 * p);
      return `rgb(${r}, ${g}, ${b})`;
    }

    if (t < 0.55) {
      const p = (t - 0.25) / 0.3;
      const r = Math.round(18 + 34 * p);
      const g = Math.round(120 + 120 * p);
      const b = Math.round(220 - 172 * p);
      return `rgb(${r}, ${g}, ${b})`;
    }

    if (t < 0.8) {
      const p = (t - 0.55) / 0.25;
      const r = Math.round(52 + 203 * p);
      const g = Math.round(240 - 28 * p);
      const b = Math.round(48 - 30 * p);
      return `rgb(${r}, ${g}, ${b})`;
    }

    const p = (t - 0.8) / 0.2;
    const r = 255;
    const g = Math.round(212 - 144 * p);
    const b = Math.round(18 * (1 - p));
    return `rgb(${r}, ${g}, ${b})`;
  }

  function sendConfig() {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(
      JSON.stringify({
        type: 'set_config',
        center_hz: centerHz,
        bandwidth_hz: Math.max(2_000_000, bandwidthHz),
      })
    );
  }

  function drawRow(dbfs: number[]) {
    const ctx = canvasEl?.getContext('2d');
    if (!ctx) return;

    const width = canvasEl.clientWidth;
    const height = plotHeight;

    ctx.drawImage(canvasEl, 0, 0, width, height - 1, 0, 1, width, height - 1);

    for (let x = 0; x < width; x++) {
      const idx = Math.floor((x / width) * dbfs.length);
      const value = dbfs[Math.min(dbfs.length - 1, idx)] ?? -120;
      ctx.fillStyle = colorForDbfs(value);
      ctx.fillRect(x, 0, 1, 1);
    }
  }

  function connect() {
    if (socket) socket.close();

    socket = new WebSocket(wsUrl);

    socket.addEventListener('open', () => {
      connected = true;
      reconnectAttempts = 0;
      sendConfig();
    });

    socket.addEventListener('message', (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type !== 'spectrum' || !Array.isArray(payload.dbfs)) return;

        frameRateHz = payload.frame_rate_hz ?? frameRateHz;
        sourceMode = payload.source ?? sourceMode;
        drawRow(payload.dbfs as number[]);
      } catch {
        // Ignore malformed websocket messages to keep stream rendering.
      }
    });

    socket.addEventListener('close', () => {
      connected = false;
      sourceMode = 'reconnecting';
      reconnectAttempts += 1;

      const delay = Math.min(5_000, 500 + reconnectAttempts * 400);
      reconnectTimer = setTimeout(connect, delay);
    });

    socket.addEventListener('error', () => {
      connected = false;
      sourceMode = 'error';
    });
  }

  $: if (connected) {
    sendConfig();
  }

  $: leftHz = centerHz - bandwidthHz / 2;
  $: rightHz = centerHz + bandwidthHz / 2;
  $: visibleSeconds = Math.max(1, Math.round(plotHeight / frameRateHz));

  onMount(() => {
    setCanvasSize();
    connect();

    const resizeObserver = new ResizeObserver(() => setCanvasSize());
    resizeObserver.observe(canvasEl);

    return () => {
      resizeObserver.disconnect();
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  });
</script>

<div class="waterfall-panel">
  <div class="meta-row">
    <span class:up={connected} class:down={!connected}>{connected ? 'WS LIVE' : 'WS OFFLINE'}</span>
    <span>{sourceMode.toUpperCase()}</span>
    <span>{formatMHz(centerHz)} center</span>
    <span>{(bandwidthHz / 1_000_000).toFixed(1)} MHz span</span>
  </div>

  <div class="axis-row">
    <span>{formatMHz(leftHz)}</span>
    <span>{formatMHz(centerHz)}</span>
    <span>{formatMHz(rightHz)}</span>
  </div>

  <div class="plot-wrap">
    <div class="time-axis">
      <span>Now</span>
      <span>{visibleSeconds}s ago</span>
    </div>
    <canvas bind:this={canvasEl} class="waterfall-canvas" style={`height:${plotHeight}px`}></canvas>
  </div>
</div>

<style>
  .waterfall-panel {
    background: #0b1527;
    border: 1px solid #1e293b;
    border-radius: 6px;
    overflow: hidden;
  }

  .meta-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.45rem 0.75rem;
    border-bottom: 1px solid #1e293b;
    font-family: 'Fira Code', monospace;
    font-size: 0.62rem;
    color: #94a3b8;
  }

  .meta-row .up { color: #4ade80; }
  .meta-row .down { color: #ef4444; }

  .axis-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    padding: 0.35rem 0.75rem;
    border-bottom: 1px solid #1e293b;
    font-size: 0.62rem;
    color: #64748b;
    font-family: 'Fira Code', monospace;
  }

  .axis-row span:nth-child(2) {
    text-align: center;
    color: #f8fafc;
  }

  .axis-row span:last-child {
    text-align: right;
  }

  .plot-wrap {
    display: grid;
    grid-template-columns: 54px 1fr;
  }

  .time-axis {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 0.5rem 0.4rem;
    font-family: 'Fira Code', monospace;
    font-size: 0.6rem;
    color: #64748b;
    border-right: 1px solid #1e293b;
    background: #081224;
  }

  .waterfall-canvas {
    width: 100%;
    display: block;
    background: #071126;
    image-rendering: pixelated;
  }

  @media (max-width: 900px) {
    .plot-wrap {
      grid-template-columns: 44px 1fr;
    }

    .meta-row {
      flex-wrap: wrap;
      gap: 0.4rem 0.7rem;
    }
  }
</style>
