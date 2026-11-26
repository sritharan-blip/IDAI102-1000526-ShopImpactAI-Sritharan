// Draw a shaded 3D sphere in WebGL. The map rotates independently of Orbit's face.
(() => {
  const tag = "shopimpact-earth";
  const block = document.currentScript?.previousElementSibling;
  const placeholder = block?.matches(".si-earth-scene") ? block : block?.querySelector(".si-earth-model");
  if (!placeholder) return;
  if (!customElements.get(tag)) defineEarth(tag);

  // Streamlit's HTML sanitizer accepts the initial div. Upgrade it after insertion.
  const earth = document.createElement(tag);
  for (const attr of placeholder.attributes) earth.setAttribute(attr.name, attr.value);
  earth.append(...placeholder.childNodes);
  placeholder.replaceWith(earth);

function defineEarth(tag) {
  let backgroundPose;
  let surfaceImage;

  function loadEarthSurface() {
    // The same decoded satellite map is reused when Streamlit replaces the canvas.
    if (!surfaceImage) {
      const image = new Image();
      image.src = "app/static/earth-blue-marble.jpg";
      surfaceImage = image.decode().then(() => image, () => null);
    }
    return surfaceImage;
  }

  const continents = [
    [[-168,63],[-143,72],[-124,72],[-107,78],[-77,74],[-59,54],[-67,48],[-80,43],[-80,26],[-98,19],[-86,11],[-82,8],[-93,15],[-106,23],[-117,33],[-126,48],[-135,56],[-157,59]],
    [[-83,10],[-69,13],[-52,5],[-35,-7],[-42,-23],[-54,-34],[-66,-55],[-74,-48],[-74,-28],[-81,-6]],
    [[-73,60],[-57,59],[-26,69],[-21,81],[-44,85],[-63,80]],
    [[-11,36],[-10,44],[4,53],[4,60],[27,71],[43,68],[49,61],[32,46],[26,36],[14,36],[7,44],[-1,38]],
    [[-17,15],[-9,30],[7,37],[25,32],[34,30],[43,12],[51,11],[43,0],[39,-13],[32,-27],[18,-35],[12,-18],[5,4],[-7,5]],
    [[28,71],[54,73],[69,76],[111,73],[137,72],[164,66],[179,65],[169,51],[148,47],[140,40],[124,34],[121,20],[112,19],[104,9],[101,3],[95,17],[87,23],[79,8],[72,20],[64,24],[57,21],[52,14],[45,12],[37,30],[28,35],[34,46],[48,53]],
    [[112,-22],[124,-14],[135,-12],[143,-14],[150,-23],[154,-33],[147,-40],[139,-37],[131,-33],[115,-35]],
    [[130,-3],[139,-3],[151,-6],[146,-10],[136,-8]],
    [[99,5],[106,-5],[117,-7],[121,-9],[107,-8],[99,-3]],
    [[128,31],[139,38],[145,44],[144,37],[138,33]],
    [[47,-12],[50,-16],[46,-25],[43,-23]],
    [[167,-42],[174,-35],[178,-38],[171,-45],[166,-47]]
  ];

  function landTexture() {
    const texture = document.createElement("canvas");
    texture.width = 1024;
    texture.height = 512;
    const ink = texture.getContext("2d");
    const point = ([lon, lat]) => [(lon + 180) / 360 * texture.width, (90 - lat) / 180 * texture.height];
    ink.fillStyle = "#000";
    ink.fillRect(0, 0, texture.width, texture.height);
    ink.fillStyle = "#fff";
    for (const outline of continents) {
      ink.beginPath();
      outline.forEach((coordinate, index) => {
        const [x, y] = point(coordinate);
        if (index === 0) ink.moveTo(x, y);
        else ink.lineTo(x, y);
      });
      ink.fill();
    }
    ink.fillRect(0, 463, texture.width, 49);
    return texture;
  }

  const vertex = `
    attribute vec2 position;
    varying vec2 plane;
    void main() {
      plane = position;
      gl_Position = vec4(position, 0., 1.);
    }`;

  const fragment = `
    #ifdef GL_FRAGMENT_PRECISION_HIGH
    precision highp float;
    #else
    precision mediump float;
    #endif
    varying vec2 plane;
    uniform sampler2D map;
    uniform vec2 turn;
    uniform float time;
    uniform float mood;
    uniform float backdrop;
    uniform bool satellite;
    uniform float cheer;
    const float PI = 3.14159265;

    float blob(vec2 delta, vec2 size) {
      return 1. - smoothstep(.88, 1., length(delta / size));
    }

    void main() {
      float bob = (sin(time * 1.5) * .018 + cheer * .13) * (1. - backdrop);
      vec2 p = (plane - vec2(0., bob)) / mix(.73, .86, backdrop);
      float radius = length(p);
      vec3 blueAir = vec3(.24, .77, 1.);
      vec3 dirtyAir = vec3(.72, .56, .36);
      vec3 air = mix(blueAir, dirtyAir, mood);
      if (radius > 1.) {
        float outerGlow = exp(-13. * (radius - 1.)) * .48;
        float angle = atan(p.y, p.x);
        float wisps = sin(8. * angle - time) * .5 + .5;
        float distanceToBand = radius - 1.12 - .035 * sin(4. * angle + time);
        float band = exp(-65. * distanceToBand * distanceToBand);
        gl_FragColor = vec4(air, min(1., outerGlow + band * wisps * mood * .46));
        return;
      }

      // Recover the front-facing hemisphere and rotate its texture coordinates in two axes.
      vec3 n = vec3(p, sqrt(max(0., 1. - dot(p, p))));
      float tilt = turn.y;
      vec3 globe = vec3(n.x, n.y * cos(tilt) + n.z * sin(tilt), n.z * cos(tilt) - n.y * sin(tilt));
      vec2 uv = vec2(atan(globe.x, globe.z) / (2. * PI) + .5 + turn.x / (2. * PI),
                     .5 - asin(clamp(globe.y, -1., 1.)) / PI);
      vec3 surface = texture2D(map, uv).rgb;
      float land = surface.r;
      float flecks = sin(85. * uv.x + 2. * sin(17. * uv.y)) * sin(70. * uv.y + 5. * uv.x);
      float clouds = smoothstep(.55, .95, sin(33. * uv.x + time * .16 + 4. * sin(12. * uv.y))
                                           * sin(37. * uv.y + 4. * uv.x));
      vec3 water = mix(vec3(.055, .53, .90), vec3(.29, .38, .36), mood);
      vec3 ground = mix(vec3(.30, .83, .32), vec3(.52, .47, .29), mood);
      vec3 color = mix(water, ground, land) + flecks * .038;
      color = mix(color, mix(vec3(.93, .99, 1.), dirtyAir, mood), clouds * (.37 + mood * .29));
      vec3 light = normalize(vec3(-.64, .58, 1.));
      if (satellite) {
        // Lift the shaded hemisphere gently while keeping the satellite coastline detail intact.
        color = pow(surface, vec3(.79));
        color *= .73 + .40 * max(0., dot(n, light));
        color += vec3(.025, .105, .21) * pow(1. - n.z, 2.6);
        color = mix(color, vec3(.88, .96, 1.), clouds * .12);
        gl_FragColor = vec4(color, 1.);
        return;
      }
      color *= .52 + .63 * max(0., dot(n, light));
      color += air * pow(1. - n.z, 2.) * .42;
      color += vec3(.35, .43, .43) * pow(max(0., dot(n, light)), 34.) * .36;
      if (backdrop > .5) {
        gl_FragColor = vec4(color, 1.);
        return;
      }

      // Eyes and mouth sit on the lit face of the sphere so the pet remains readable while spinning.
      float expression = mix(mood, 0., cheer);
      vec2 face = p - vec2(sin(turn.x) * .055, .06);
      float blinkPhase = mod(time + 2., 4.7) - 3.7;
      float blink = 1. - .94 * exp(-145. * blinkPhase * blinkPhase);
      vec2 eye = vec2(abs(face.x) - .255, face.y - .04);
      vec3 ink = vec3(.029, .069, .11);
      color = mix(color, vec3(1., .47, .48), blob(vec2(abs(face.x) - .405, face.y + .145), vec2(.125, .060)) * (.61 - mood * .31));
      color = mix(color, ink, blob(eye, vec2(.094, .118 * blink)));
      color = mix(color, vec3(.95, 1., 1.), blob(eye - vec2(-.026, .043 * blink), vec2(.027, .027 * blink)));
      color = mix(color, vec3(.55, .84, .98), blob(eye - vec2(.035, -.038 * blink), vec2(.014, .014 * blink)) * .82);
      float smile = -.27 + mix(2.25, -1.8, expression) * face.x * face.x + expression * .065;
      float mouth = (1. - smoothstep(.024, .034, abs(face.y - smile))) * (1. - smoothstep(.156, .179, abs(face.x)));
      color = mix(color, ink, mouth);
      float brow = .202 + .42 * eye.x;
      float concern = blob(vec2(eye.x, face.y - brow), vec2(.10, .024)) * smoothstep(.42, .85, expression);
      color = mix(color, ink, concern);
      gl_FragColor = vec4(color, 1.);
    }`;

  function createRenderer(canvas, isBackground, satelliteImage) {
    const gl = canvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false });
    if (!gl) return null;
    function shader(type, source) {
      const result = gl.createShader(type);
      gl.shaderSource(result, source);
      gl.compileShader(result);
      if (!gl.getShaderParameter(result, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(result));
      return result;
    }

    const program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, vertex));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, fragment));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
    gl.useProgram(program);

    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const position = gl.getAttribLocation(program, "position");
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

    gl.bindTexture(gl.TEXTURE_2D, gl.createTexture());
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, satelliteImage ?? landTexture());
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    const turn = gl.getUniformLocation(program, "turn");
    const time = gl.getUniformLocation(program, "time");
    const mood = gl.getUniformLocation(program, "mood");
    const cheer = gl.getUniformLocation(program, "cheer");
    gl.uniform1f(gl.getUniformLocation(program, "backdrop"), Number(isBackground));
    gl.uniform1i(gl.getUniformLocation(program, "satellite"), Number(Boolean(satelliteImage)));
    let angle = 0, pitch = 0, clock = 0, level = 0, bounce = 0;
    function paint() {
      gl.uniform2f(turn, angle, pitch);
      gl.uniform1f(time, clock);
      gl.uniform1f(mood, level);
      gl.uniform1f(cheer, bounce);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
    function updateResolution() {
      // Size the backing buffer to the actual display pixels, up to a bounded GPU workload.
      const size = Math.max(1, Math.min(1440, Math.round(
        canvas.getBoundingClientRect().width * Math.min(devicePixelRatio || 1, 2))));
      if (canvas.width !== size || canvas.height !== size) {
        canvas.width = size;
        canvas.height = size;
      }
      gl.viewport(0, 0, size, size);
      paint();
    }
    updateResolution();
    const resize = new ResizeObserver(updateResolution);
    resize.observe(canvas);
    return {
      draw(yaw, tilt, elapsed, moodLevel, joy = 0) {
        angle = yaw;
        pitch = tilt;
        clock = elapsed;
        level = moodLevel;
        bounce = joy;
        paint();
      },
      release() {
        resize.disconnect();
        gl.getExtension("WEBGL_lose_context")?.loseContext();
      }
    };
  }

  customElements.define(tag, class extends HTMLElement {
    connectedCallback() {
      this.raf = requestAnimationFrame(() => this.mount());
    }

    async mount() {
      const canvas = this.querySelector("canvas");
      if (!canvas) return;
      const isBackground = this.dataset.background === "1";
      const satelliteImage = isBackground ? await loadEarthSurface() : null;
      if (!this.isConnected) return;
      try {
        this.renderer = createRenderer(canvas, isBackground, satelliteImage);
      } catch (error) {
        console.warn("Orbit could not initialize WebGL", error);
      }
      if (!this.renderer) return;
      this.dataset.ready = "true";
      if (satelliteImage) this.dataset.texture = "blue-marble";
      const media = matchMedia("(prefers-reduced-motion: reduce)");
      if (isBackground) {
        this.mountBackground(media);
        return;
      }
      const level = { bright: 0, watch: .48, hazy: 1 }[this.dataset.mood];
      let yaw = -1.12;
      let tilt = .20;
      let elapsed = 0;
      let lastTime = 0;
      let pointer;
      let lastTap;
      let celebrationStarted = -Infinity;
      const reduced = () => media.matches || this.dataset.reduce === "1";
      const draw = () => {
        const progress = Math.min((performance.now() - celebrationStarted) / 950, 1);
        const joy = reduced() ? 0 : Math.pow(Math.sin(progress * Math.PI), 1.4);
        const wiggle = joy * Math.sin(progress * Math.PI * 3) * .22;
        this.renderer.draw(yaw + wiggle, tilt, elapsed, level, joy);
      };
      const celebrate = () => {
        celebrationStarted = performance.now();
        const burst = this.querySelector(".si-earth-confetti");
        burst.replaceChildren(...Array.from({length: 9}, (_, index) => {
          const particle = document.createElement("i");
          const angle = index / 9 * Math.PI * 2;
          const distance = index % 2 ? 98 : 72;
          particle.textContent = index % 3 ? "✦" : "✧";
          particle.style.setProperty("--dx", `${Math.round(Math.cos(angle) * distance)}px`);
          particle.style.setProperty("--dy", `${Math.round(Math.sin(angle) * distance)}px`);
          return particle;
        }));
        this.dataset.celebrating = "true";
        clearTimeout(this.celebrationTimer);
        this.celebrationTimer = setTimeout(() => {
          delete this.dataset.celebrating;
          burst.replaceChildren();
        }, 950);
      };
      const run = (now) => {
        const delta = lastTime ? Math.min((now - lastTime) / 1000, .05) : 0;
        lastTime = now;
        if (!reduced()) {
          elapsed += delta;
          if (pointer === undefined) yaw = (yaw + delta * .16) % (Math.PI * 2);
          draw();
        }
        this.raf = requestAnimationFrame(run);
      };
      const adjust = (dx, dy) => {
        yaw = (yaw + dx) % (Math.PI * 2);
        tilt = Math.max(-1.10, Math.min(1.10, tilt + dy));
        draw();
      };
      canvas.addEventListener("pointerdown", (event) => {
        pointer = { id: event.pointerId, x: event.clientX, y: event.clientY, travel: 0 };
        canvas.setPointerCapture(event.pointerId);
      });
      canvas.addEventListener("pointermove", (event) => {
        if (pointer?.id !== event.pointerId) return;
        const dx = event.clientX - pointer.x;
        const dy = event.clientY - pointer.y;
        pointer.travel += Math.hypot(dx, dy);
        adjust(-dx * .017, dy * .017);
        pointer.x = event.clientX;
        pointer.y = event.clientY;
      });
      canvas.addEventListener("pointerup", (event) => {
        if (pointer?.id !== event.pointerId || pointer.travel > 12) {
          lastTap = undefined;
          return;
        }
        const tap = { time: performance.now(), x: event.clientX, y: event.clientY };
        if (lastTap && tap.time - lastTap.time <= 380 && Math.hypot(tap.x - lastTap.x, tap.y - lastTap.y) <= 28) {
          lastTap = undefined;
          celebrate();
        } else {
          lastTap = tap;
        }
      });
      canvas.addEventListener("lostpointercapture", () => { pointer = undefined; });
      canvas.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          if (!event.repeat) celebrate();
          return;
        }
        const steps = { ArrowLeft: [-.22, 0], ArrowRight: [.22, 0], ArrowUp: [0, -.16], ArrowDown: [0, .16] };
        if (!(event.key in steps)) return;
        event.preventDefault();
        adjust(...steps[event.key]);
      });
      draw();
      this.visibility = new IntersectionObserver(([entry]) => {
        cancelAnimationFrame(this.raf);
        lastTime = 0;
        if (entry.isIntersecting && !reduced()) this.raf = requestAnimationFrame(run);
      });
      this.visibility.observe(canvas);
      this.motionChanged = () => {
        cancelAnimationFrame(this.raf);
        lastTime = 0;
        if (!reduced()) this.raf = requestAnimationFrame(run);
        else draw();
      };
      this.motionMedia = media;
      media.addEventListener("change", this.motionChanged);
    }

    mountBackground(media) {
      const target = { yaw: Number(this.dataset.yaw), tilt: Number(this.dataset.tilt) };
      const from = backgroundPose ?? target;
      // Take the shortest turn across the longitude seam and start from the last painted angle.
      const delta = Math.atan2(Math.sin(target.yaw - from.yaw), Math.cos(target.yaw - from.yaw));
      const start = performance.now();
      const reduced = () => media.matches || this.dataset.reduce === "1";
      let lastPaint = -Infinity;
      const draw = (now) => {
        if (!reduced() && now - lastPaint < 30) {
          this.raf = requestAnimationFrame(draw);
          return;
        }
        lastPaint = now;
        const progress = reduced() ? 1 : Math.min((now - start) / 820, 1);
        const ease = progress * progress * (3 - 2 * progress);
        const yaw = from.yaw + delta * ease;
        const tilt = from.tilt + (target.tilt - from.tilt) * ease;
        backgroundPose = { yaw, tilt };
        this.renderer.draw(yaw, tilt, reduced() ? 0 : now / 1000, 0);
        if (!reduced()) this.raf = requestAnimationFrame(draw);
      };
      this.motionMedia = media;
      this.motionChanged = () => {
        cancelAnimationFrame(this.raf);
        draw(performance.now());
      };
      media.addEventListener("change", this.motionChanged);
      draw(start);
    }

    disconnectedCallback() {
      cancelAnimationFrame(this.raf);
      clearTimeout(this.celebrationTimer);
      this.visibility?.disconnect();
      this.motionMedia?.removeEventListener("change", this.motionChanged);
      this.renderer?.release();
    }
  });
}
})();
