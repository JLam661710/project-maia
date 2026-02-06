let bokehs = [];
let particles = [];
let agents = [];
let agentImages = {};

function preload() {
  // 加载图片
  agentImages.interviewer = loadImage('Agents 的头像们/访谈猿interviewer-头像光圈.png');
  agentImages.summary = loadImage('Agents 的头像们/总结蜂summary-头像光圈.png');
  agentImages.judge = loadImage('Agents 的头像们/审判鹳judge-头像光圈.png');
  agentImages.analyst = loadImage('Agents 的头像们/分析狮analyst-头像光圈.png');
  agentImages.architect = loadImage('Agents 的头像们/方案狸architect-头像光圈.png');
}

function setup() {
  let canvas = createCanvas(windowWidth, windowHeight);
  canvas.parent('sketch-container');
  
  // 初始化大光斑 (Bokeh)
  // 创建暖色调光斑
  for (let i = 0; i < 12; i++) {
    bokehs.push(new Bokeh('warm'));
  }
  // 创建冷色调光斑
  for (let i = 0; i < 8; i++) {
    bokehs.push(new Bokeh('cool'));
  }
  
  // 初始化小粒子 (Particles)
  for (let i = 0; i < 50; i++) {
    particles.push(new Particle());
  }

  // 初始化 Agents
  initAgents();
}

function initAgents() {
  agents = [];
  // 基于窗口大小计算相对位置
  let w = width;
  let h = height;
  
  // 中间：访谈猿 (最大)
  agents.push(new Agent(agentImages.interviewer, w * 0.5, h * 0.45, 270));
  
  // 左上：总结蜂 (中小)
  agents.push(new Agent(agentImages.summary, w * 0.25, h * 0.25, 165));
  
  // 左下：审判鹳 (中)
  agents.push(new Agent(agentImages.judge, w * 0.35, h * 0.65, 210));
  
  // 右上：分析狮 (中)
  agents.push(new Agent(agentImages.analyst, w * 0.75, h * 0.3, 210));
  
  // 右下：方案狸 (小)
  agents.push(new Agent(agentImages.architect, w * 0.65, h * 0.75, 150));
}

function draw() {
  clear(); // 清除每一帧，保持背景透明
  
  // 使用 ADD 模式让重叠的光斑更亮，模拟发光效果
  // 注意：在透明背景上，这只会影响 canvas 内部元素的混合
  blendMode(ADD);
  
  for (let b of bokehs) {
    b.update();
    b.display();
  }
  
  // 恢复默认混合模式给粒子，或者继续使用 ADD
  blendMode(BLEND); 
  for (let p of particles) {
    p.update();
    p.display();
  }

  // 绘制 Agents (使用普通混合模式)
  for (let agent of agents) {
    agent.update();
    agent.display();
  }
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
  initAgents(); // 窗口大小改变时重新计算位置
}

class Agent {
  constructor(img, x, y, size) {
    this.img = img;
    this.basePos = createVector(x, y);
    this.pos = this.basePos.copy();
    this.size = size;
    this.floatOffset = random(1000); // 随机相位，避免同步移动
  }

  update() {
    // 仅在 Y 轴方向轻微漂浮
    // sin() 产生周期性运动，frameCount * 0.02 控制速度，* 10 控制幅度
    let floatY = sin(frameCount * 0.03 + this.floatOffset) * 8;
    this.pos.y = this.basePos.y + floatY;
  }

  display() {
    imageMode(CENTER);
    // 绘制图片
    image(this.img, this.pos.x, this.pos.y, this.size, this.size);
  }
}


class Bokeh {
  constructor(type) {
    this.pos = createVector(random(width), random(height));
    // 减弱初始速度，使用 Perlin noise 需要的 offset
    this.noiseOffset = createVector(random(1000), random(1000)); 
    this.baseSize = random(60, 180); // 光斑大小
    this.size = this.baseSize;
    this.type = type;
    
    // 根据类型设置颜色
    if (this.type === 'warm') {
      // 橙色、金色、琥珀色
      // 颜色格式: R, G, B, Alpha (透明度低一些以获得柔和感)
      this.color = color(255, random(120, 180), random(20, 80), random(100, 180));
    } else {
      // 青色、深蓝、紫色
      this.color = color(random(40, 100), random(100, 200), 255, random(80, 150));
    }
  }

  update() {
    // 使用 Perlin Noise 实现缓慢、有机的漂浮移动
    let nX = noise(this.noiseOffset.x);
    let nY = noise(this.noiseOffset.y);
    
    // 映射 noise (0-1) 到速度向量 (-0.5 到 0.5)
    let vel = createVector(map(nX, 0, 1, -0.5, 0.5), map(nY, 0, 1, -0.5, 0.5));
    this.pos.add(vel);
    
    // 缓慢更新 noise offset
    this.noiseOffset.add(0.005, 0.005);
    
    // 鼠标交互：鼠标附近的斥力/扰动 (减弱力度)
    let mouse = createVector(mouseX, mouseY);
    let dir = p5.Vector.sub(this.pos, mouse);
    let d = dir.mag();
    
    // 如果鼠标靠近 (300像素内)
    if (d < 300 && d > 0) {
      dir.normalize();
      // 距离越近，斥力越强，但整体力度减小
      let force = map(d, 0, 300, 0.8, 0); 
      dir.mult(force);
      this.pos.add(dir);
    }
    
    // 边界检查：无限循环
    if (this.pos.x < -this.size) this.pos.x = width + this.size;
    if (this.pos.x > width + this.size) this.pos.x = -this.size;
    if (this.pos.y < -this.size) this.pos.y = height + this.size;
    if (this.pos.y > height + this.size) this.pos.y = -this.size;
    
    // 动态呼吸效果：大小随时间微调，速度也减慢
    this.size = this.baseSize + sin(frameCount * 0.01 + this.pos.x) * 10;
  }

  display() {
    noStroke();
    
    // 使用 Radial Gradient 模拟柔和的渐隐边缘
    let ctx = drawingContext;
    let gradient = ctx.createRadialGradient(
      this.pos.x, this.pos.y, 0,
      this.pos.x, this.pos.y, this.size / 2
    );
    
    // 中心颜色
    gradient.addColorStop(0, this.color.toString());
    
    // 边缘完全透明，中间加一层过渡
    let c = this.color;
    gradient.addColorStop(0.4, `rgba(${red(c)}, ${green(c)}, ${blue(c)}, ${alpha(c) * 0.5 / 255})`);
    gradient.addColorStop(1, `rgba(${red(c)}, ${green(c)}, ${blue(c)}, 0)`);
    
    ctx.fillStyle = gradient;
    circle(this.pos.x, this.pos.y, this.size);
  }
}

class Particle {
  constructor() {
    this.pos = createVector(random(width), random(height));
    this.vel = p5.Vector.random2D().mult(random(0.1, 0.3));
    this.size = random(1, 3);
    this.initialAlpha = random(100, 200);
  }
  
  update() {
    this.pos.add(this.vel);
    
    if (this.pos.x < 0) this.pos.x = width;
    if (this.pos.x > width) this.pos.x = 0;
    if (this.pos.y < 0) this.pos.y = height;
    if (this.pos.y > height) this.pos.y = 0;
  }
  
  display() {
    noStroke();
    // 闪烁效果
    let a = this.initialAlpha + sin(frameCount * 0.05 + this.pos.x) * 50;
    fill(255, 255, 255, a);
    circle(this.pos.x, this.pos.y, this.size);
  }
}
