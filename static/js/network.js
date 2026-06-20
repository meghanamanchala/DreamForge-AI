const canvas = document.getElementById("neuralCanvas");
const ctx = canvas.getContext("2d");

let width = (canvas.width = window.innerWidth);
let height = (canvas.height = window.innerHeight);

window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
});

const nodes = [];
const nodeCount = 60;
const connectionDistance = 120;

// Mouse coordinates
const mouse = { x: null, y: null };
window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});
window.addEventListener("mouseout", () => {
    mouse.x = null;
    mouse.y = null;
});

// Initialize nodes
for (let i = 0; i < nodeCount; i++) {
    nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 2 + 1,
    });
}

function animate() {
    ctx.clearRect(0, 0, width, height);

    // Draw lines & update node positions
    for (let i = 0; i < nodes.length; i++) {
        const n1 = nodes[i];
        n1.x += n1.vx;
        n1.y += n1.vy;

        // Bounce on boundaries
        if (n1.x < 0 || n1.x > width) n1.vx *= -1;
        if (n1.y < 0 || n1.y > height) n1.vy *= -1;

        // Draw dot
        ctx.beginPath();
        ctx.arc(n1.x, n1.y, n1.radius, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(168, 85, 247, 0.5)"; // purple dot
        ctx.fill();

        // Connect nodes
        for (let j = i + 1; j < nodes.length; j++) {
            const n2 = nodes[j];
            const dx = n1.x - n2.x;
            const dy = n1.y - n2.y;
            const dist = Math.sqrt(dx * dx + dx * dx); // wait, math: dx*dx + dy*dy! Let's write dy*dy
            const realDist = Math.sqrt(dx * dx + dy * dy);

            if (realDist < connectionDistance) {
                const alpha = (1 - realDist / connectionDistance) * 0.15;
                ctx.beginPath();
                ctx.moveTo(n1.x, n1.y);
                ctx.lineTo(n2.x, n2.y);
                ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`; // indigo line
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
        }

        // Connect to mouse pointer
        if (mouse.x !== null && mouse.y !== null) {
            const mdx = n1.x - mouse.x;
            const mdy = n1.y - mouse.y;
            const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
            if (mdist < 150) {
                const malpha = (1 - mdist / 150) * 0.25;
                ctx.beginPath();
                ctx.moveTo(n1.x, n1.y);
                ctx.lineTo(mouse.x, mouse.y);
                ctx.strokeStyle = `rgba(168, 85, 247, ${malpha})`; // purple link to cursor
                ctx.stroke();
            }
        }
    }

    requestAnimationFrame(animate);
}

// Start Canvas loop
animate();
