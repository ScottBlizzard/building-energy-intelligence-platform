<script setup>
import { computed, reactive, ref } from "vue";

const props = defineProps({
  buildings: {
    type: Array,
    default: () => []
  },
  floorSummary: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["select-floor"]);

const rotation = ref(-34);
const pitch = ref(58);
const dragState = reactive({
  active: false,
  moved: false,
  startX: 0,
  startY: 0,
  startRotation: 0,
  startPitch: 58
});

const buildingProfiles = {
  "BLD-A": { x: -230, y: -70, width: 92, depth: 110, floors: 5, shortName: "教学楼A", accent: "#43d7a0" },
  "BLD-B": { x: -54, y: 96, width: 78, depth: 92, floors: 4, shortName: "办公楼B", accent: "#64b5f6" },
  "BLD-C": { x: 122, y: -78, width: 104, depth: 116, floors: 5, shortName: "图书楼C", accent: "#ffd166" },
  "BLD-D": { x: 260, y: 92, width: 86, depth: 104, floors: 6, shortName: "实验楼D", accent: "#ff8a65" }
};

const riskIndex = computed(() => {
  const index = new Map();
  props.floorSummary.forEach((item) => {
    const key = `${item.building_id}::${normalizeFloorLabel(item.floor_label)}`;
    const current = index.get(key) || {
      anomalyCount: 0,
      anomalyRate: 0,
      electricityKwh: 0,
      filterLabel: item.floor_label,
      zoneName: item.zone_name
    };

    index.set(key, {
      anomalyCount: current.anomalyCount + Number(item.anomaly_count || 0),
      anomalyRate: Math.max(current.anomalyRate, Number(item.anomaly_rate || 0)),
      electricityKwh: current.electricityKwh + Number(item.electricity_kwh || 0),
      filterLabel: current.filterLabel || item.floor_label,
      zoneName: current.zoneName || item.zone_name
    });
  });
  return index;
});

const sceneBuildings = computed(() => {
  const sourceBuildings = props.buildings.length ? props.buildings : uniqueBuildingsFromSummary();

  return sourceBuildings.map((building, index) => {
    const profile = buildingProfiles[building.building_id] || {
      x: -180 + index * 120,
      y: index % 2 ? 80 : -60,
      width: 82,
      depth: 96,
      floors: inferFloorCount(building.building_name),
      shortName: building.building_name,
      accent: "#0f8b8d"
    };
    const floors = buildFloorStack(building, profile.floors);
    const anomalyCount = floors.reduce((sum, floor) => sum + floor.anomalyCount, 0);

    return {
      ...building,
      ...profile,
      floors,
      anomalyCount,
      riskFloorCount: floors.filter((floor) => floor.risk).length
    };
  });
});

const riskFloorTotal = computed(() =>
  sceneBuildings.value.reduce((sum, building) => sum + building.riskFloorCount, 0)
);

const totalAnomalyCount = computed(() =>
  sceneBuildings.value.reduce((sum, building) => sum + building.anomalyCount, 0)
);

function uniqueBuildingsFromSummary() {
  const map = new Map();
  props.floorSummary.forEach((item) => {
    map.set(item.building_id, {
      building_id: item.building_id,
      building_name: item.building_name,
      building_type: ""
    });
  });
  return Array.from(map.values());
}

function inferFloorCount(buildingName = "") {
  if (buildingName.includes("实验")) {
    return 6;
  }
  if (buildingName.includes("教学") || buildingName.includes("图书")) {
    return 5;
  }
  return 4;
}

function buildFloorStack(building, floorCount) {
  const labels = ["B1", ...Array.from({ length: floorCount }, (_, index) => `${index + 1}F`), "RF"];
  return labels.map((label) => {
    const risk = riskIndex.value.get(`${building.building_id}::${label}`);
    const anomalyCount = Number(risk?.anomalyCount || 0);
    const anomalyRate = Number(risk?.anomalyRate || 0);

    return {
      label,
      filterLabel: risk?.filterLabel || label,
      zoneName: risk?.zoneName || "未检出异常",
      risk: anomalyCount > 0,
      highRisk: anomalyRate >= 22 || anomalyCount >= 20,
      anomalyCount,
      anomalyRate,
      electricityKwh: Number(risk?.electricityKwh || 0)
    };
  });
}

function normalizeFloorLabel(label = "") {
  const value = String(label);
  if (value.includes("B1")) {
    return "B1";
  }
  if (value.includes("RF")) {
    return "RF";
  }
  const match = value.match(/\d+F/);
  return match ? match[0] : value;
}

function buildingStyle(building) {
  return {
    transform: `translate3d(${building.x}px, ${building.y}px, 0)`,
    "--tower-width": `${building.width}px`,
    "--tower-depth": `${building.depth}px`,
    "--accent-color": building.accent
  };
}

function floorStyle(floor, index) {
  const safeTop = "rgba(60, 224, 155, 0.9)";
  const safeSide = "rgba(18, 119, 84, 0.9)";
  const riskTop = floor.highRisk ? "rgba(255, 57, 73, 0.96)" : "rgba(255, 124, 76, 0.94)";
  const riskSide = floor.highRisk ? "rgba(136, 18, 36, 0.95)" : "rgba(150, 69, 38, 0.92)";

  return {
    "--level": index,
    "--floor-top": floor.risk ? riskTop : safeTop,
    "--floor-side": floor.risk ? riskSide : safeSide,
    "--floor-glow": floor.risk ? "rgba(255, 67, 78, 0.5)" : "rgba(60, 224, 155, 0.3)"
  };
}

function floorTitle(building, floor) {
  const state = floor.risk
    ? `异常 ${floor.anomalyCount} 条，异常率 ${floor.anomalyRate}%`
    : "未发现异常";
  return `${building.building_name} ${floor.filterLabel}：${state}`;
}

function selectFloor(building, floor) {
  if (dragState.moved) {
    dragState.moved = false;
    return;
  }

  emit("select-floor", {
    buildingId: building.building_id,
    buildingName: building.building_name,
    floorLabel: floor.filterLabel,
    floorDisplay: floor.label
  });
}

function startDrag(event) {
  dragState.active = true;
  dragState.moved = false;
  dragState.startX = event.clientX;
  dragState.startY = event.clientY;
  dragState.startRotation = rotation.value;
  dragState.startPitch = pitch.value;
  event.currentTarget.setPointerCapture?.(event.pointerId);
}

function moveDrag(event) {
  if (!dragState.active) {
    return;
  }
  const deltaX = event.clientX - dragState.startX;
  const deltaY = event.clientY - dragState.startY;
  if (Math.abs(deltaX) + Math.abs(deltaY) > 5) {
    dragState.moved = true;
  }
  rotation.value = dragState.startRotation + deltaX * 0.45;
  pitch.value = clamp(dragState.startPitch - deltaY * 0.12, 46, 68);
}

function endDrag(event) {
  dragState.active = false;
  event.currentTarget.releasePointerCapture?.(event.pointerId);
}

function resetView() {
  rotation.value = -34;
  pitch.value = 58;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}
</script>

<template>
  <div class="risk-scene">
    <div class="risk-scene__topbar">
      <div>
        <strong>校园楼宇三维风险态势</strong>
        <span>拖拽旋转视图，点击楼层可跳转到数据浏览并自动筛选。</span>
      </div>
      <div class="scene-metrics">
        <span>风险楼层 <b>{{ riskFloorTotal }}</b></span>
        <span>异常记录 <b>{{ totalAnomalyCount }}</b></span>
        <button type="button" @click="resetView">复位视角</button>
      </div>
    </div>

    <div
      class="risk-scene__viewport"
      :class="{ 'is-dragging': dragState.active }"
      @pointerdown="startDrag"
      @pointermove="moveDrag"
      @pointerup="endDrag"
      @pointercancel="endDrag"
    >
      <div v-if="loading" class="risk-scene__loading">正在加载楼宇态势...</div>
      <div class="scene-orb scene-orb--one"></div>
      <div class="scene-orb scene-orb--two"></div>
      <div
        class="risk-scene__world"
        :style="{ transform: `rotateX(${pitch}deg) rotateZ(${rotation}deg)` }"
      >
        <div class="campus-ground">
          <div class="campus-road campus-road--main"></div>
          <div class="campus-road campus-road--cross"></div>
          <div class="campus-lake"></div>
          <div class="campus-grid"></div>
          <div
            v-for="building in sceneBuildings"
            :key="building.building_id"
            class="scene-building"
            :style="buildingStyle(building)"
          >
            <div class="building-shadow"></div>
            <div class="building-base"></div>
            <div class="building-stack">
              <button
                v-for="(floor, index) in building.floors"
                :key="`${building.building_id}-${floor.label}`"
                type="button"
                class="floor-block"
                :class="{
                  'floor-block--risk': floor.risk,
                  'floor-block--high': floor.highRisk
                }"
                :style="floorStyle(floor, index)"
                :title="floorTitle(building, floor)"
                @pointerdown.stop
                @click.stop="selectFloor(building, floor)"
              >
                <span>{{ floor.label }}</span>
              </button>
            </div>
            <div class="building-pin">
              <strong>{{ building.shortName }}</strong>
              <span>{{ building.riskFloorCount }} 个风险楼层</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="risk-scene__legend">
      <span><i class="legend-dot legend-dot--safe"></i>正常楼层</span>
      <span><i class="legend-dot legend-dot--risk"></i>风险楼层</span>
      <span><i class="legend-dot legend-dot--high"></i>高风险楼层</span>
      <span>俯角 {{ Math.round(pitch) }}° / 旋转 {{ Math.round(rotation % 360) }}°</span>
    </div>
  </div>
</template>

<style scoped>
.risk-scene {
  display: grid;
  gap: 14px;
}

.risk-scene__topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.risk-scene__topbar strong {
  display: block;
  color: #0e3540;
  font-size: 18px;
  margin-bottom: 4px;
}

.risk-scene__topbar span {
  color: #5f737b;
  font-size: 13px;
}

.scene-metrics {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.scene-metrics span,
.scene-metrics button {
  border: 1px solid rgba(15, 139, 141, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: #0f6b67;
  font: inherit;
  padding: 8px 13px;
}

.scene-metrics b {
  color: #b92736;
}

.scene-metrics button {
  cursor: pointer;
}

.risk-scene__viewport {
  position: relative;
  min-height: 500px;
  overflow: hidden;
  border-radius: 34px;
  cursor: grab;
  perspective: 1300px;
  background:
    radial-gradient(circle at 20% 20%, rgba(122, 244, 210, 0.28), transparent 26%),
    radial-gradient(circle at 72% 18%, rgba(255, 209, 102, 0.22), transparent 24%),
    radial-gradient(circle at 72% 76%, rgba(80, 142, 255, 0.16), transparent 28%),
    linear-gradient(145deg, #06151d 0%, #102d38 44%, #dfeee5 100%);
  box-shadow: inset 0 0 90px rgba(255, 255, 255, 0.08);
  user-select: none;
  touch-action: none;
}

.risk-scene__viewport.is-dragging {
  cursor: grabbing;
}

.risk-scene__loading {
  position: absolute;
  inset: 18px auto auto 18px;
  z-index: 4;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: #183642;
  padding: 8px 14px;
  font-size: 13px;
}

.scene-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(2px);
  opacity: 0.5;
  pointer-events: none;
}

.scene-orb--one {
  width: 210px;
  height: 210px;
  left: 8%;
  top: 16%;
  background: radial-gradient(circle, rgba(90, 232, 184, 0.38), transparent 64%);
}

.scene-orb--two {
  width: 260px;
  height: 260px;
  right: 8%;
  bottom: 8%;
  background: radial-gradient(circle, rgba(255, 204, 112, 0.28), transparent 64%);
}

.risk-scene__world {
  position: absolute;
  left: 50%;
  top: 54%;
  width: 0;
  height: 0;
  transform-style: preserve-3d;
  transition: transform 0.08s linear;
}

.campus-ground {
  position: absolute;
  width: 760px;
  height: 520px;
  left: -380px;
  top: -260px;
  border-radius: 54px;
  background:
    linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px),
    linear-gradient(0deg, rgba(255,255,255,0.08) 1px, transparent 1px),
    linear-gradient(135deg, rgba(28, 108, 97, 0.88), rgba(25, 54, 62, 0.96));
  background-size: 44px 44px, 44px 44px, auto;
  box-shadow: 0 42px 120px rgba(0, 0, 0, 0.38);
  transform-style: preserve-3d;
}

.campus-grid {
  position: absolute;
  inset: 34px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 40px;
  box-shadow: inset 0 0 34px rgba(255, 255, 255, 0.08);
}

.campus-road {
  position: absolute;
  z-index: 0;
  background: rgba(232, 238, 222, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.campus-road--main {
  left: 72px;
  right: 72px;
  top: 238px;
  height: 34px;
  border-radius: 999px;
}

.campus-road--cross {
  left: 348px;
  top: 54px;
  bottom: 54px;
  width: 34px;
  border-radius: 999px;
}

.campus-lake {
  position: absolute;
  right: 72px;
  top: 210px;
  width: 128px;
  height: 74px;
  border-radius: 48% 52% 44% 56%;
  background: linear-gradient(135deg, rgba(92, 203, 255, 0.42), rgba(15, 107, 103, 0.2));
  border: 1px solid rgba(174, 231, 255, 0.35);
  box-shadow: inset 0 0 24px rgba(180, 243, 255, 0.18);
}

.scene-building {
  position: absolute;
  z-index: 2;
  left: 50%;
  top: 50%;
  width: var(--tower-width);
  height: var(--tower-depth);
  transform-style: preserve-3d;
}

.building-stack {
  position: absolute;
  inset: 0;
  transform-style: preserve-3d;
}

.building-shadow {
  position: absolute;
  inset: 18px -22px -22px 18px;
  border-radius: 26px;
  background: rgba(0, 0, 0, 0.28);
  filter: blur(11px);
  transform: translateZ(-4px);
}

.building-base {
  position: absolute;
  inset: -12px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.18), rgba(0, 0, 0, 0.12));
  border: 1px solid rgba(255, 255, 255, 0.14);
  transform: translateZ(-3px);
}

.floor-block {
  position: absolute;
  inset: 0;
  border: 1px solid rgba(255, 255, 255, 0.26);
  border-radius: 14px;
  padding: 0;
  cursor: pointer;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.42), transparent 34%),
    repeating-linear-gradient(90deg, rgba(255,255,255,0.12) 0 2px, transparent 2px 12px),
    var(--floor-top);
  box-shadow:
    0 0 28px var(--floor-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.38);
  transform: translateZ(calc(var(--level) * 19px));
  transform-style: preserve-3d;
}

.floor-block:hover {
  outline: 2px solid rgba(255, 255, 255, 0.78);
  filter: brightness(1.12);
}

.floor-block::before,
.floor-block::after {
  content: "";
  position: absolute;
  background: var(--floor-side);
  opacity: 0.95;
}

.floor-block::before {
  left: 0;
  right: 0;
  bottom: -13px;
  height: 13px;
  transform-origin: top;
  transform: rotateX(-90deg);
  border-radius: 0 0 11px 11px;
}

.floor-block::after {
  top: 0;
  right: -13px;
  width: 13px;
  height: 100%;
  transform-origin: left;
  transform: rotateY(90deg);
  border-radius: 0 11px 11px 0;
}

.floor-block span {
  position: absolute;
  left: 8px;
  top: 7px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.36);
}

.floor-block--risk {
  animation: riskPulse 1.8s ease-in-out infinite;
}

.floor-block--high {
  animation-duration: 1.15s;
}

.building-pin {
  position: absolute;
  left: 50%;
  top: 50%;
  min-width: 116px;
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.15), transparent),
    rgba(7, 28, 35, 0.76);
  color: white;
  padding: 8px 10px;
  text-align: center;
  transform: translate3d(-50%, -50%, 176px) rotateZ(34deg);
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.24);
}

.building-pin::before {
  content: "";
  display: block;
  width: 34px;
  height: 3px;
  margin: 0 auto 7px;
  border-radius: 999px;
  background: var(--accent-color);
  box-shadow: 0 0 14px var(--accent-color);
}

.building-pin strong,
.building-pin span {
  display: block;
}

.building-pin strong {
  font-size: 13px;
}

.building-pin span {
  color: rgba(255, 255, 255, 0.74);
  font-size: 11px;
  margin-top: 2px;
}

.risk-scene__legend {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  color: #5f737b;
  font-size: 13px;
}

.risk-scene__legend span {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.legend-dot {
  width: 11px;
  height: 11px;
  border-radius: 999px;
  display: inline-block;
}

.legend-dot--safe {
  background: #3ce09b;
  box-shadow: 0 0 12px rgba(60, 224, 155, 0.5);
}

.legend-dot--risk {
  background: #ff7c4c;
  box-shadow: 0 0 12px rgba(255, 124, 76, 0.5);
}

.legend-dot--high {
  background: #ff3949;
  box-shadow: 0 0 12px rgba(255, 57, 73, 0.58);
}

@keyframes riskPulse {
  0%, 100% {
    filter: saturate(1);
  }
  50% {
    filter: saturate(1.35) brightness(1.1);
  }
}

@media (max-width: 768px) {
  .risk-scene__viewport {
    min-height: 390px;
  }

  .campus-ground {
    transform: scale(0.78);
  }
}
</style>
