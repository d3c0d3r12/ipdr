<template>
  <div class="cyber-background">
    <!-- Animated Grid Lines -->
    <div class="grid-overlay"></div>
    
    <!-- Circular HUD Elements -->
    <div class="hud-circle hud-1">
      <div class="circle-ring"></div>
      <div class="circle-ring ring-2"></div>
      <div class="circle-center"></div>
      <div class="crosshair"></div>
    </div>
    
    <div class="hud-circle hud-2">
      <div class="circle-ring"></div>
      <div class="circle-center"></div>
    </div>
    
    <!-- Corner Brackets -->
    <div class="corner-bracket top-left"></div>
    <div class="corner-bracket top-right"></div>
    <div class="corner-bracket bottom-left"></div>
    <div class="corner-bracket bottom-right"></div>
    
    <!-- Data Panels -->
    <div class="data-panel panel-left">
      <div class="panel-line" v-for="i in 8" :key="'left-' + i" :style="{ animationDelay: `${i * 0.2}s` }"></div>
    </div>
    
    <div class="data-panel panel-right">
      <div class="panel-line" v-for="i in 8" :key="'right-' + i" :style="{ animationDelay: `${i * 0.2}s` }"></div>
    </div>
    
    <!-- Target Markers -->
    <div class="target-marker marker-1">
      <div class="marker-cross"></div>
      <div class="marker-text">TARGET LOCATED</div>
    </div>
    
    <div class="target-marker marker-2">
      <div class="marker-cross"></div>
      <div class="marker-text">SCANNING...</div>
    </div>
    
    <!-- Scanning Lines -->
    <div class="scan-line horizontal"></div>
    <div class="scan-line vertical"></div>
    
    <!-- Glowing Particles -->
    <div class="particles">
      <div class="particle" v-for="i in 20" :key="i" :style="getParticleStyle(i)"></div>
    </div>
    
    <!-- Center Text Overlay -->
    <div class="center-overlay">
      <div class="login-prompt">PLEASE LOGIN BELOW</div>
      <div class="restricted-text">RESTRICTED ACCESS ONLY</div>
      <div class="system-status">SYSTEM ACTIVE</div>
    </div>
    
    <!-- Biometric Handprint Scanner (Right Side) -->
    <div class="handprint-scanner">
      <div class="hand-icon">
        <svg viewBox="0 0 100 120" class="hand-svg">
          <!-- Thumb -->
          <ellipse cx="25" cy="70" rx="8" ry="20" fill="none" stroke="rgba(0, 200, 255, 0.6)" stroke-width="1.5"/>
          <!-- Index finger -->
          <ellipse cx="40" cy="30" rx="6" ry="25" fill="none" stroke="rgba(0, 200, 255, 0.6)" stroke-width="1.5"/>
          <!-- Middle finger -->
          <ellipse cx="50" cy="25" rx="6" ry="28" fill="none" stroke="rgba(0, 200, 255, 0.6)" stroke-width="1.5"/>
          <!-- Ring finger -->
          <ellipse cx="60" cy="30" rx="6" ry="25" fill="none" stroke="rgba(0, 200, 255, 0.6)" stroke-width="1.5"/>
          <!-- Pinky -->
          <ellipse cx="70" cy="40" rx="5" ry="20" fill="none" stroke="rgba(0, 200, 255, 0.6)" stroke-width="1.5"/>
          <!-- Palm -->
          <ellipse cx="50" cy="75" rx="20" ry="25" fill="none" stroke="rgba(0, 200, 255, 0.6)" stroke-width="1.5"/>
          <!-- Fingerprint lines -->
          <circle cx="50" cy="75" r="5" fill="none" stroke="rgba(0, 200, 255, 0.4)" stroke-width="0.5"/>
          <circle cx="50" cy="75" r="8" fill="none" stroke="rgba(0, 200, 255, 0.4)" stroke-width="0.5"/>
          <circle cx="50" cy="75" r="11" fill="none" stroke="rgba(0, 200, 255, 0.4)" stroke-width="0.5"/>
        </svg>
      </div>
      <div class="scanner-text">SUBJECT IDENTIFIED</div>
      <div class="scanner-status">BIOMETRIC SCAN COMPLETE</div>
    </div>
    
    <!-- World Map Outline -->
    <div class="world-map">
      <svg viewBox="0 0 1000 500" class="map-svg">
        <!-- Simplified world map continents -->
        <path d="M 200,150 L 250,140 L 280,160 L 300,150 L 320,170 L 300,190 L 280,180 L 250,200 L 220,180 Z" 
              fill="none" stroke="rgba(0, 200, 255, 0.2)" stroke-width="1"/>
        <path d="M 400,200 L 450,180 L 500,190 L 520,210 L 500,240 L 470,250 L 440,240 L 420,220 Z" 
              fill="none" stroke="rgba(0, 200, 255, 0.2)" stroke-width="1"/>
        <path d="M 600,180 L 680,170 L 720,190 L 740,220 L 720,250 L 680,260 L 640,250 L 620,220 Z" 
              fill="none" stroke="rgba(0, 200, 255, 0.2)" stroke-width="1"/>
        <!-- Grid lines on map -->
        <line x1="0" y1="150" x2="1000" y2="150" stroke="rgba(0, 200, 255, 0.1)" stroke-width="0.5"/>
        <line x1="0" y1="250" x2="1000" y2="250" stroke="rgba(0, 200, 255, 0.1)" stroke-width="0.5"/>
        <line x1="250" y1="0" x2="250" y2="500" stroke="rgba(0, 200, 255, 0.1)" stroke-width="0.5"/>
        <line x1="500" y1="0" x2="500" y2="500" stroke="rgba(0, 200, 255, 0.1)" stroke-width="0.5"/>
        <line x1="750" y1="0" x2="750" y2="500" stroke="rgba(0, 200, 255, 0.1)" stroke-width="0.5"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
const getParticleStyle = (index: number) => {
  const size = Math.random() * 3 + 1
  const left = Math.random() * 100
  const top = Math.random() * 100
  const duration = Math.random() * 3 + 2
  const delay = Math.random() * 2
  
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    top: `${top}%`,
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`
  }
}
</script>

<style scoped>
.cyber-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
  pointer-events: none;
  background: #000000;
}

/* Grid Overlay */
.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 150, 200, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 150, 200, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 30s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

/* HUD Circles */
.hud-circle {
  position: absolute;
  width: 200px;
  height: 200px;
  border: 2px solid rgba(0, 200, 255, 0.3);
  border-radius: 50%;
  animation: rotateHUD 20s linear infinite;
}

.hud-1 {
  top: 10%;
  left: 15%;
}

.hud-2 {
  bottom: 15%;
  right: 20%;
  width: 150px;
  height: 150px;
}

.circle-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: 80%;
  border: 1px solid rgba(0, 200, 255, 0.4);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.ring-2 {
  width: 60%;
  height: 60%;
  animation-delay: 0.5s;
}

.circle-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 10px;
  height: 10px;
  background: rgba(0, 200, 255, 0.8);
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(0, 200, 255, 0.8);
}

.crosshair {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
}

.crosshair::before,
.crosshair::after {
  content: '';
  position: absolute;
  background: rgba(0, 200, 255, 0.3);
}

.crosshair::before {
  top: 50%;
  left: 0;
  width: 100%;
  height: 1px;
}

.crosshair::after {
  top: 0;
  left: 50%;
  width: 1px;
  height: 100%;
}

@keyframes rotateHUD {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.8; transform: translate(-50%, -50%) scale(1.05); }
}

/* Corner Brackets */
.corner-bracket {
  position: absolute;
  width: 40px;
  height: 40px;
  border: 2px solid rgba(0, 200, 255, 0.5);
  animation: bracketPulse 2s ease-in-out infinite;
}

.top-left {
  top: 20px;
  left: 20px;
  border-right: none;
  border-bottom: none;
}

.top-right {
  top: 20px;
  right: 20px;
  border-left: none;
  border-bottom: none;
}

.bottom-left {
  bottom: 20px;
  left: 20px;
  border-right: none;
  border-top: none;
}

.bottom-right {
  bottom: 20px;
  right: 20px;
  border-left: none;
  border-top: none;
}

@keyframes bracketPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; box-shadow: 0 0 10px rgba(0, 200, 255, 0.5); }
}

/* Data Panels */
.data-panel {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100px;
  height: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  background: rgba(0, 20, 40, 0.3);
  border: 1px solid rgba(0, 200, 255, 0.2);
}

.panel-left {
  left: 20px;
}

.panel-right {
  right: 20px;
}

.panel-line {
  height: 2px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(0, 200, 255, 0.6), 
    transparent
  );
  animation: dataFlow 2s ease-in-out infinite;
}

@keyframes dataFlow {
  0%, 100% { opacity: 0.3; transform: scaleX(0.5); }
  50% { opacity: 1; transform: scaleX(1); }
}

/* Target Markers */
.target-marker {
  position: absolute;
  width: 60px;
  height: 60px;
  animation: targetBlink 3s ease-in-out infinite;
}

.marker-1 {
  top: 30%;
  left: 40%;
}

.marker-2 {
  bottom: 35%;
  right: 30%;
}

.marker-cross {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border: 2px solid rgba(255, 50, 50, 0.6);
  border-radius: 50%;
}

.marker-cross::before,
.marker-cross::after {
  content: '';
  position: absolute;
  background: rgba(255, 50, 50, 0.6);
}

.marker-cross::before {
  top: 50%;
  left: 10%;
  width: 80%;
  height: 2px;
  transform: translateY(-50%);
}

.marker-cross::after {
  top: 10%;
  left: 50%;
  width: 2px;
  height: 80%;
  transform: translateX(-50%);
}

.marker-text {
  position: absolute;
  top: -25px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: rgba(255, 50, 50, 0.8);
  white-space: nowrap;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 5px rgba(255, 50, 50, 0.5);
}

@keyframes targetBlink {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* Scanning Lines */
.scan-line {
  position: absolute;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(0, 200, 255, 0.5), 
    transparent
  );
  box-shadow: 0 0 15px rgba(0, 200, 255, 0.5);
}

.scan-line.horizontal {
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  animation: scanHorizontal 8s linear infinite;
}

.scan-line.vertical {
  top: 0;
  left: 0;
  width: 2px;
  height: 100%;
  animation: scanVertical 10s linear infinite;
}

@keyframes scanHorizontal {
  0% { top: 0; opacity: 0; }
  5% { opacity: 1; }
  95% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

@keyframes scanVertical {
  0% { left: 0; opacity: 0; }
  5% { opacity: 1; }
  95% { opacity: 1; }
  100% { left: 100%; opacity: 0; }
}

/* Particles */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.particle {
  position: absolute;
  background: rgba(0, 200, 255, 0.6);
  border-radius: 50%;
  animation: particleFloat 3s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(0, 200, 255, 0.8);
}

@keyframes particleFloat {
  0%, 100% { opacity: 0; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-20px); }
}

/* Center Overlay */
.center-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  opacity: 0.2;
  z-index: 10;
}

.login-prompt {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(0, 200, 255, 0.7);
  font-family: 'Courier New', monospace;
  letter-spacing: 0.2em;
  text-shadow: 0 0 15px rgba(0, 200, 255, 0.4);
  margin-bottom: 1.5rem;
  animation: promptPulse 2s ease-in-out infinite;
}

.restricted-text {
  font-size: 2rem;
  font-weight: 700;
  color: rgba(0, 200, 255, 0.8);
  font-family: 'Courier New', monospace;
  letter-spacing: 0.3em;
  text-shadow: 0 0 20px rgba(0, 200, 255, 0.5);
  animation: textGlow 2s ease-in-out infinite;
  margin-bottom: 1rem;
}

.system-status {
  font-size: 0.875rem;
  color: rgba(0, 255, 100, 0.6);
  font-family: 'Courier New', monospace;
  letter-spacing: 0.2em;
  animation: statusBlink 1.5s ease-in-out infinite;
}

@keyframes promptPulse {
  0%, 100% { opacity: 0.6; text-shadow: 0 0 15px rgba(0, 200, 255, 0.4); }
  50% { opacity: 1; text-shadow: 0 0 25px rgba(0, 200, 255, 0.7); }
}

@keyframes textGlow {
  0%, 100% { text-shadow: 0 0 20px rgba(0, 200, 255, 0.3); }
  50% { text-shadow: 0 0 30px rgba(0, 200, 255, 0.6); }
}

@keyframes statusBlink {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* Biometric Handprint Scanner */
.handprint-scanner {
  position: absolute;
  top: 30%;
  right: 10%;
  width: 200px;
  text-align: center;
  animation: scannerPulse 3s ease-in-out infinite;
}

.hand-icon {
  width: 120px;
  height: 140px;
  margin: 0 auto 1rem;
  filter: drop-shadow(0 0 15px rgba(0, 200, 255, 0.6));
}

.hand-svg {
  width: 100%;
  height: 100%;
  animation: handGlow 2s ease-in-out infinite;
}

@keyframes handGlow {
  0%, 100% { filter: drop-shadow(0 0 10px rgba(0, 200, 255, 0.4)); }
  50% { filter: drop-shadow(0 0 20px rgba(0, 200, 255, 0.8)); }
}

.scanner-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(0, 200, 255, 0.8);
  font-family: 'Courier New', monospace;
  letter-spacing: 0.1em;
  text-shadow: 0 0 10px rgba(0, 200, 255, 0.5);
  margin-bottom: 0.5rem;
}

.scanner-status {
  font-size: 0.625rem;
  color: rgba(0, 255, 100, 0.6);
  font-family: 'Courier New', monospace;
  letter-spacing: 0.05em;
  animation: statusBlink 1.5s ease-in-out infinite;
}

@keyframes scannerPulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

/* World Map */
.world-map {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: 60%;
  opacity: 0.15;
  pointer-events: none;
}

.map-svg {
  width: 100%;
  height: 100%;
  animation: mapPulse 4s ease-in-out infinite;
}

@keyframes mapPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* Responsive */
@media (max-width: 768px) {
  .hud-circle {
    width: 120px;
    height: 120px;
  }
  
  .data-panel {
    width: 60px;
    height: 120px;
  }
  
  .restricted-text {
    font-size: 1rem;
  }
  
  .login-prompt {
    font-size: 0.875rem;
  }
  
  .target-marker {
    width: 40px;
    height: 40px;
  }
  
  .handprint-scanner {
    width: 120px;
    right: 5%;
  }
  
  .hand-icon {
    width: 80px;
    height: 100px;
  }
  
  .world-map {
    width: 90%;
    height: 50%;
  }
}
</style>
