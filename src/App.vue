<!-- ************************ Script ************************ -->
<script setup>

// ***** import component packages ***** //
import * as THREE from "three"
console.log(THREE);
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { ref, watch } from "vue";
import mqtt from "mqtt";  // Import MQTT.js
console.log(mqtt);

// ***** MQTT Configuration ***** //
let mqttClient = null;
const options = {
  port:8083,
  connectTimeout:4000,
  clientId:"Digital Mine _ " + Math.random().toString(16).substring(2, 8),
}
const brokerUrl = "ws://10.0.0.223/mqtt";  // MQTT broker address
const topicName = "truck1_position";       // Topic for truck1's position


// ***** MQTT Connection & Subscription ***** //
function connectMQTT() {
  mqttClient = mqtt.connect(brokerUrl, options);

  mqttClient.on("connect", () => {
    console.log("✅ MQTT Connected successfully");
    mqttClient.subscribe(topicName, (err) => {
      if (!err) {
        console.log(`📡 Subscription Success: ${topicName}`);
      } else {
        console.error("❌ Subscription Failed", err);
      }
    });
  });

  mqttClient.on("message", (topic, message) => {
    if (topic === topicName && Truck_1) {
      try {
        const position = JSON.parse(message.toString());
        if (position.x !== undefined && position.y !== undefined && position.z !== undefined) {
          Truck_1.position.set(position.x, position.y, position.z);
          console.log(`📍 Truck_1 Location Updates: x=${position.x}, y=${position.y}, z=${position.z}`);
        }
      } catch (error) {
        console.error("❌ Unable to parse MQTT messages:", error);
      }
    }
  });

  mqttClient.on("error", (error) => {
    console.error("❌ MQTT connection error:", error);
  });

  mqttClient.on("close", () => {
    console.log("🔌 Disconnect from MQTT");
  });
}

// ***** 启动 MQTT 连接 ***** //
connectMQTT();

// ***** 初始化 Three.js 的基本设置 ***** //
// Initialize GLTF Loader
const GLoader = new GLTFLoader();

// Initialize scene, camera, and renderer
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 10000);
camera.position.set(5, 6, 20);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setClearColor(0x041316);                                 // set background color and size - renderer 0x161819
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById("app").appendChild(renderer.domElement);  // add a renderer.domElement under the "app" div (webg1 canvas)

// 添加环境光和方向光
const light = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(light);
const dirlight = new THREE.DirectionalLight('rgb(253,253,253)',10);
dirlight.position.set(10, 10, 10).normalize(); // 设置方向光的位置
scene.add(dirlight);

// Add orbit controller
const orbitcontroller = new OrbitControls(camera, renderer.domElement); //orbit controller
orbitcontroller.enableDamping = true;
orbitcontroller.enableZoom = true;
orbitcontroller.enablePan = true;

// Camera transition properties
let cameraFocusTarget = new THREE.Vector3(0, 0, 0);
let isTransitioning = false;

// Add coordinate system and grid
const axesHelper = new THREE.AxesHelper(5);
scene.add(axesHelper);
var gridHelper = new THREE.GridHelper(20,20);
// scene.add(gridHelper);

// ***** Initialize World and Trucks ***** //
let MineWorld = new THREE.Group();
let Truck_1 = null;
let Truck_2 = null;
let Loader_1 = null;
scene.add(MineWorld);

// Labels array
const labels = [];

// Track selected car
const selectedCar = ref("Free View");

// Define splines and movement properties
let spline_1, spline_2, spline_3;
let progress1 = 0, progress2 = 0.2, progress3 = 0;            // 物体运动时在运动路径的初始位置，范围0~1
const clock = new THREE.Clock();  // Initialize clock
// console.log(clock);
const frequency = 16/1000;                     // 16 ms
const velocity1 = 0.0001, velocity2 = 0.0001, velocity3 = 0.00012;  // 影响运动速率的一个值，范围0~1，需要和渲染频率结合计算才能得到真正的速率

// ***** Load MineWorld Model ***** //
// Load .glb/.gltf model - demo map
GLoader.load(
  './public/MineWorld/MineDemo.gltf',
  function(gltf){
    console.log('MineWorld', gltf.scene);
    gltf.scene.traverse(function (obj){
      if (obj.isMesh){
        obj.material = new THREE.MeshBasicMaterial({
          color: 0x004444,
          wireframe:false,
          transparent:true,
          opacity:0.6
        });
        obj.geometry.computeVertexNormals();
        try {
          const edges = new THREE.EdgesGeometry(obj.geometry, 1);
          const edgesMaterial = new THREE.LineBasicMaterial({
            color: 0xd9dcdf,
            transparent: true,
            opacity: 0.08
          });
          const line = new THREE.LineSegments(edges, edgesMaterial);
          obj.add(line);
        } catch (error) {
          console.error("❌ error:", obj, error);
        }
      }
    });
    const LoopX = gltf.scene.getObjectByName("Text_-_LoopX");
    LoopX.material.color.set(0x45818e);
    const Logo = gltf.scene.getObjectByName("LoopXsvg");
    Logo.material.color.set(0xe06666);
    const DigitalMine = gltf.scene.getObjectByName("Text_-_3D_Digital_Mine");
    DigitalMine.material.color.set(0x134f5c);
    MineWorld.add(gltf.scene);
  },
  function(xhr){
    const percent = xhr.loaded/xhr.total;
    console.log('Loading MineWorld %' + percent*100);
  }
);

// ***** Load Vehicle Model - Truck_1 ***** //
// Load .glb/.gltf model - truck
GLoader.load(
  './public/Truck_1/Truck_1.gltf',
  function(gltf){
    console.log('Truck_1', gltf);
    Truck_1 = gltf.scene;
    Truck_1.name = "Truck 1";
    Truck_1.position.set(-21,2.8,12);
    Truck_1.rotation.set(0,-45,0);
    Truck_1.scale.set(0.8,0.8,0.8);
    scene.add(Truck_1);
    addLabel(Truck_1, "Truck 1");
  },
  function(xhr){
    const percent = xhr.loaded/xhr.total;
    console.log('Loading Truck_1 %' + percent*100);
  }
);

// 创建轨迹 - 车辆的移动轨迹
spline_1 = new THREE.CatmullRomCurve3([
new THREE.Vector3(-21,2.8,12),
new THREE.Vector3(-22,2.8,12.5),
new THREE.Vector3(-23,2.8,13),
new THREE.Vector3(-24,2.8,13.5),
new THREE.Vector3(-25,2.8,14),
new THREE.Vector3(-26,2.9,14.5),
new THREE.Vector3(-27,3.0,15),
new THREE.Vector3(-28,3.0,16),
new THREE.Vector3(-29,3.0,16.5),
new THREE.Vector3(-30,3.0,17),
new THREE.Vector3(-31,3.0,17.5),
new THREE.Vector3(-32,3.0,18),
new THREE.Vector3(-34,3.0,19),
new THREE.Vector3(-36,3.1,20),
new THREE.Vector3(-38,3.2,21),
new THREE.Vector3(-40,3.2,22),
new THREE.Vector3(-42,3.2,23),
new THREE.Vector3(-44,3.2,24),
new THREE.Vector3(-46,3.2,25),
new THREE.Vector3(-48,3.3,26),
new THREE.Vector3(-50,3.4,27),
new THREE.Vector3(-52,3.5,28),
new THREE.Vector3(-55,3.6,30),
new THREE.Vector3(-58,3.6,31),
new THREE.Vector3(-64,3.6,34),
new THREE.Vector3(-68,3.6,34),
new THREE.Vector3(-72,3.6,35),
new THREE.Vector3(-76,3.6,36),
new THREE.Vector3(-83,3.4,37),
new THREE.Vector3(-90,2.8,37.5),
new THREE.Vector3(-95,1.8,38),
new THREE.Vector3(-100,1.0,39),
new THREE.Vector3(-110,0.8,40),
new THREE.Vector3(-130,-1.5,42),
new THREE.Vector3(-150,-3.0,44),
new THREE.Vector3(-170,-5.0,46),
new THREE.Vector3(-190,-7.0,48),
new THREE.Vector3(-210,-8.0,50),
new THREE.Vector3(-220,-9.0,52),
new THREE.Vector3(-230,-10.0,50),
new THREE.Vector3(-235,-12.0,48),
new THREE.Vector3(-240,-14.0,44),
new THREE.Vector3(-245,-18.0,38),
new THREE.Vector3(-246,-22.0,30),
new THREE.Vector3(-242,-28.0,22),
new THREE.Vector3(-230,-34.0,16),
new THREE.Vector3(-225,-36.0,15),
new THREE.Vector3(-200,-42.0,22),
]);
spline_1.curveType = 'catmullrom'
spline_1.closed = false //设置是否闭环
spline_1.tension = 0.5 //设置线的张力，0为无弧度折线
// 为曲线添加材质在场景中显示出来，方便看到轨迹线
const curve_points1 = spline_1.getPoints(50) // 50等分获取曲线点
const curve_geometry1 = new THREE.BufferGeometry().setFromPoints(curve_points1);
const curve_material1 = new THREE.LineBasicMaterial({color: 0x6a329f});
// Create the final object to add to the scene
const curveObject1 = new THREE.Line(curve_geometry1, curve_material1);
scene.add(curveObject1) // 添加到场景中

// ***** Load Vehicle Model - Truck_2 ***** //
GLoader.load(
  './public/Truck_1/Truck_1.gltf',
  function(gltf){
    console.log('Truck_2', gltf);
    Truck_2 = gltf.scene;
    Truck_2.name = "Truck 2";
    Truck_2.position.set(-21,2.8,12);
    Truck_2.rotation.set(0,-45,0);
    Truck_2.scale.set(0.8,0.8,0.8);
    scene.add(Truck_2);
    addLabel(Truck_2, "Truck 2");
  },
  function(xhr){
    const percent = xhr.loaded/xhr.total;
    console.log('Loading Truck_2 %' + percent*100);
  }
);

// 创建轨迹 - 车辆的移动轨迹
spline_2 = spline_1.clone();
spline_2.curveType = 'catmullrom'
spline_2.closed = false //设置是否闭环
spline_2.tension = 0.5 //设置线的张力，0为无弧度折线
// 为曲线添加材质在场景中显示出来，方便看到轨迹线
const curve_points2 = spline_2.getPoints(50) // 50等分获取曲线点
const curve_geometry2 = new THREE.BufferGeometry().setFromPoints(curve_points2);
const curve_material2 = new THREE.LineBasicMaterial({color: 0x6a329f});
// Create the final object to add to the scene
const curveObject2 = new THREE.Line(curve_geometry2, curve_material2);
scene.add(curveObject2) // 添加到场景中

// ***** Load Vehicle Model - Loader_1 ***** //
GLoader.load(
  './public/Loader242D/Loader242D.gltf',
  function(gltf){
    console.log('Loader_1', gltf);
    Loader_1 = gltf.scene;
    Loader_1.name = "Loader 1";
    Loader_1.position.set(-85,19,82);
    Loader_1.rotation.set(0,0,0);
    Loader_1.scale.set(0.8,0.8,0.8);
    scene.add(Loader_1);
    addLabel(Loader_1, "Loader 1");
  },
  function(xhr){
    const percent = xhr.loaded/xhr.total;
    console.log('Loading Loader_1 %' + percent*100);
  }
);

// 创建轨迹 - 车辆的移动轨迹
spline_3 = new THREE.CatmullRomCurve3([
new THREE.Vector3(-85,19,82),
new THREE.Vector3(-86,17.5,78),
new THREE.Vector3(-87,15.5,72),
new THREE.Vector3(-87,13,66),
new THREE.Vector3(-87.5,11,60),
new THREE.Vector3(-88,8,50),
new THREE.Vector3(-89,6,46),
new THREE.Vector3(-90,4,42),
new THREE.Vector3(-94,2,38),
new THREE.Vector3(-100,1.0,39),
new THREE.Vector3(-110,0.8,40),
new THREE.Vector3(-130,-1.5,42),
new THREE.Vector3(-150,-3.0,44),
new THREE.Vector3(-170,-5.0,46),
new THREE.Vector3(-190,-7.0,48),
new THREE.Vector3(-210,-8.0,50),
new THREE.Vector3(-220,-9.0,52),
new THREE.Vector3(-230,-10.0,50),
new THREE.Vector3(-235,-12.0,48),
new THREE.Vector3(-240,-14.0,44),
new THREE.Vector3(-245,-18.0,38),
new THREE.Vector3(-246,-22.0,30),
new THREE.Vector3(-242,-28.0,22),
new THREE.Vector3(-230,-34.0,16),
new THREE.Vector3(-225,-36.0,15),
new THREE.Vector3(-200,-42.0,22),
]);
spline_3.curveType = 'catmullrom'
spline_3.closed = false //设置是否闭环
spline_3.tension = 0.5 //设置线的张力，0为无弧度折线
// 为曲线添加材质在场景中显示出来，方便看到轨迹线
const curve_points3 = spline_3.getPoints(50) // 50等分获取曲线点
const curve_geometry3 = new THREE.BufferGeometry().setFromPoints(curve_points3);
const curve_material3 = new THREE.LineBasicMaterial({color: 0xe69138});
// Create the final object to add to the scene
const curveObject3 = new THREE.Line(curve_geometry3, curve_material3);
scene.add(curveObject3) // 添加到场景中

// ***** Move Trucks Along Their Paths ***** //
function moveOnCurve(truck, spline, progress, velocity, rotate) {
  if (!spline || !truck) return progress; // Ensure model & path exist
  const delta = clock.getDelta();  // Time elapsed since last frame 
  // console.log(delta);
  if (progress <= 1 - velocity) {
    const point = spline.getPointAt(progress);                 //获取样条曲线指定点坐标
    const nextPoint = spline.getPointAt(progress + velocity);  //获取样条曲线指定点坐标
    if (point && nextPoint) {
      truck.position.copy(point);
      truck.lookAt(nextPoint); // Orient truck towards movement direction
      truck.rotateY(rotate);
      // Calculate speed (velocity * scaling factor for realism)
      const distance = nextPoint.distanceTo(point);
      const speed = (distance / frequency * 3.6).toFixed(2);
      // Update label text dynamically
      if (truck.userData.label) {
        const pos = truck.position;
        const text = `${truck.name}\nSpeed: ${speed} km/h\nPos: (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`;
        updateLabel(truck.userData.label, text);
      }
    }
    return progress + velocity;
  } else {
    return 0; // Reset movement loop
  }
}

// ***** Create 3D Labels Above Cars ***** //
function createTextSprite(text) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  canvas.width = 400;
  canvas.height = 200;

  ctx.fillStyle = "#000000";    // "#051619"
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.font = "Bold 32px Arial"; // Larger text
  ctx.fillStyle = "#ffffff";
  // ctx.fillText(text, 20, 80);
  ctx.textAlign = "left";      // Left align text
  ctx.textBaseline = "middle"; // Center vertically

  const lines = text.split("\n");
  lines.forEach((line, i) => {
    ctx.fillText(line, 20, canvas.height / 2 - (lines.length - 1) * 25 + i * 50);
  });

  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });

  const sprite = new THREE.Sprite(material);
  sprite.scale.set(16, 8, 2); // Larger label
  return sprite;
}

// ***** Add Dynamic Labels to Cars ***** //
function addLabel(car, name) {
  const label = createTextSprite(`${name}\nSpeed: 0 m/s\nPos: (0, 0, 0)`);
  label.position.set(0, 8, 0); // Label appears higher above the truck
  car.add(label);
  car.userData.label = label;
}

// ***** Update Label Text ***** //
function updateLabel(label, text) {
  const canvas = label.material.map.image;
  const ctx = canvas.getContext("2d");

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.font = "Bold 32px Arial";
  ctx.fillStyle = "#ffffff";
  ctx.textAlign = "left";  
  ctx.textBaseline = "middle";

  const lines = text.split("\n");
  lines.forEach((line, i) => {
    ctx.fillText(line, 20, canvas.height / 2 - (lines.length - 1) * 25 + i * 50);
  });

  label.material.map.needsUpdate = true;
}

// ***** Camera Transition Logic ***** //
watch(selectedCar, (newView) => {
  let targetPosition, focusPoint;

  if (newView.includes("Truck 1") && Truck_1) {
  targetPosition = Truck_1.position.clone().add(new THREE.Vector3(16, 8, 16));
  focusPoint = Truck_1.position;
} else if (newView.includes("Truck 2") && Truck_2) {
  targetPosition = Truck_2.position.clone().add(new THREE.Vector3(16, 8, 16));
  focusPoint = Truck_2.position;
} else if (newView.includes("Loader 1") && Loader_1) {
  targetPosition = Loader_1.position.clone().add(new THREE.Vector3(16, 8, 16));
  focusPoint = Loader_1.position;
} else {
  targetPosition = new THREE.Vector3(26, 12, 24);
  focusPoint = new THREE.Vector3(-10, 10, 10);
}

  isTransitioning = true;
  animateCameraTransition(targetPosition, focusPoint);
});

function animateCameraTransition(targetPosition, focusPoint) {
  const duration = 1.5; // Animation duration in seconds
  let elapsedTime = 0;
  const startCameraPos = camera.position.clone();
  const startFocus = orbitcontroller.target.clone();

  function animate() {
    elapsedTime += frequency;
    const t = Math.min(elapsedTime / duration, 1); // Progress between 0 and 1

    // Smooth interpolation
    camera.position.lerpVectors(startCameraPos, targetPosition, t);
    orbitcontroller.target.lerpVectors(startFocus, focusPoint, t);

    if (t < 1) {
      requestAnimationFrame(animate);
    } else {
      isTransitioning = false;
    }
  }

  animate();
}

// ***** Render Loop ***** //
function render(){

  orbitcontroller.update();

  if (Truck_1 && Truck_1.userData.label) {
    const pos = Truck_1.position;
    const text = `Truck 1\nSpeed: 0 km/h\nPos: (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`;
    updateLabel(Truck_1.userData.label, text);
  }
  // progress1 = moveOnCurve(Truck_1, spline_1, progress1, velocity1, 0);  
  progress2 = moveOnCurve(Truck_2, spline_2, progress2, velocity2, 0);
  progress3 = moveOnCurve(Loader_1, spline_3, progress3, velocity3, Math.PI);
  
  if (selectedCar.value === "Follow Truck 1" && Truck_1) {
    cameraFocusTarget = Truck_1.position.clone().add(new THREE.Vector3(16, 8, 16));
    camera.position.lerp(cameraFocusTarget, 0.5);
    camera.lookAt(Truck_1.position);
  } else if (selectedCar.value === "Follow Truck 2" && Truck_2) {
    cameraFocusTarget = Truck_2.position.clone().add(new THREE.Vector3(16, 8, 16));
    camera.position.lerp(cameraFocusTarget, 0.5);
    camera.lookAt(Truck_2.position);
  } else if (selectedCar.value === "Follow Loader 1" && Loader_1) {
    cameraFocusTarget = Loader_1.position.clone().add(new THREE.Vector3(16, 8, 16));
    camera.position.lerp(cameraFocusTarget, 0.5);
    camera.lookAt(Loader_1.position);
  }
  
  renderer.render(scene,camera);
  requestAnimationFrame(render); // Web API request the next frame still using render function 
}
render();

// ***** Window Resize Handling ***** //
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
})
</script>

<!-- ************************ Template ************************ -->
<template>
  <div id="app"></div>
  <div class="selection-panel">
    <label>Select View: </label>
    <select v-model="selectedCar">
      <option> Free View </option>
      <option> Truck 1 </option>
      <option> Follow Truck 1 </option>
      <option> Truck 2 </option>
      <option> Follow Truck 2 </option>
      <option> Loader 1 </option>
      <option> Follow Loader 1 </option>
    </select>
  </div>
</template>


<!-- ************************ Style ************************ -->
<style scoped>
body {
  margin: 0;
  overflow: hidden;
}

.selection-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  padding: 10px;
  color: white;
  border-radius: 5px;
}
</style>
