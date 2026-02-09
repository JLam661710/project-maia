import Sketch from "react-p5";

export default function MaiaCanvas({ getAudioData }) {
    let particles = [];

    const setup = (p5, canvasParentRef) => {
        p5.createCanvas(window.innerWidth, window.innerHeight).parent(canvasParentRef);
        p5.noStroke();
        
        // Init particles
        for(let i=0; i<50; i++) {
            particles.push({
                x: p5.random(p5.width),
                y: p5.random(p5.height),
                size: p5.random(2, 5),
                speedX: p5.random(-0.5, 0.5),
                speedY: p5.random(-0.5, 0.5),
                alpha: p5.random(50, 150)
            });
        }
    };

    const draw = (p5) => {
        p5.background(10, 10, 20); // Deep dark blue/black
        
        // Get Audio Level
        let audioLevel = 0;
        if (getAudioData) {
            const data = getAudioData();
            if (data && data.length > 0) {
                let sum = 0;
                for(let i=0; i<data.length; i++) sum += data[i];
                audioLevel = sum / data.length; // 0-255
            }
        }
        
        let audioMod = audioLevel * 0.5;

        // Breathing Center Light (Maia's Core)
        let time = p5.millis() * 0.001;
        
        // Layer 1: Core
        let size1 = 80 + p5.sin(time * 2) * 10 + audioMod;
        let alpha1 = 200 + p5.sin(time * 2) * 55 + audioLevel * 0.5;
        p5.fill(220, 240, 255, alpha1);
        p5.ellipse(p5.width/2, p5.height/2, size1, size1);
        
        // Layer 2: Glow
        let size2 = 120 + p5.sin(time * 2 + 0.5) * 20 + audioMod * 1.5;
        let alpha2 = 100 + p5.sin(time * 2) * 30 + audioLevel * 0.3;
        p5.fill(100, 180, 255, alpha2 * 0.5);
        p5.ellipse(p5.width/2, p5.height/2, size2, size2);

        // Layer 3: Outer Aura
        let size3 = 200 + p5.sin(time * 1.5) * 30 + audioMod * 2;
        p5.fill(50, 100, 200, 30);
        p5.ellipse(p5.width/2, p5.height/2, size3, size3);

        // Particles
        particles.forEach(p => {
            p.x += p.speedX;
            p.y += p.speedY;
            
            // Wrap around screen
            if(p.x < 0) p.x = p5.width;
            if(p.x > p5.width) p.x = 0;
            if(p.y < 0) p.y = p5.height;
            if(p.y > p5.height) p.y = 0;
            
            // Twinkle
            let twinkle = p5.sin(time * 5 + p.x) * 50;
            p5.fill(255, 255, 255, p.alpha + twinkle);
            p5.ellipse(p.x, p.y, p.size);
        });
    };
    
    const windowResized = (p5) => {
        p5.resizeCanvas(window.innerWidth, window.innerHeight);
    }

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, zIndex: -1 }}>
            <Sketch setup={setup} draw={draw} windowResized={windowResized} />
        </div>
    );
}
