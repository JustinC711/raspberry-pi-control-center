// Find our canvas in the HTML
const canvas = document.getElementById("space-canvas");

// Get the 2D drawing tools
const ctx = canvas.getContext("2d");

// Set the canvas size to match the screen
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Generate 150 randomly positioned stars
for (let i = 0; i < 150; i++) {

    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height;

    const radius = Math.random() * 1.2 + 0.2;
    const brightness = Math.random() * 0.5 + 0.2;

    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);

    ctx.fillStyle = `rgba(235, 235, 240, ${brightness})`;
    ctx.fill();
}