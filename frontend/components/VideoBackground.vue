<template>
  <div class="video-background">
    <video
      v-if="videoSrc"
      autoplay
      loop
      muted
      playsinline
      class="video-bg"
      @error="onVideoError"
    >
      <source :src="videoSrc" type="video/mp4" />
      Your browser does not support the video tag.
    </video>
    <div class="video-overlay"></div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  videoSrc: {
    type: String,
    default: '/background-video.mp4'
  },
  opacity: {
    type: Number,
    default: 0.15
  }
})

const onVideoError = (error: Event) => {
  console.warn('Video background failed to load:', error)
}
</script>

<style scoped>
.video-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
  pointer-events: none;
}

.video-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  min-width: 100%;
  min-height: 100%;
  width: auto;
  height: auto;
  transform: translate(-50%, -50%);
  object-fit: cover;
  opacity: v-bind(opacity);
  filter: blur(2px) brightness(0.4);
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    180deg,
    rgba(12, 10, 9, 0.7) 0%,
    rgba(12, 10, 9, 0.85) 50%,
    rgba(12, 10, 9, 0.95) 100%
  );
  pointer-events: none;
}

/* Fallback for browsers that don't support video */
@supports not (object-fit: cover) {
  .video-bg {
    display: none;
  }
}
</style>
