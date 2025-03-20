const map = (x, in_min, in_max, out_min, out_max) => (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
const constrain = (n, min, max) => Math.min(Math.max(n, min), max);

const SARIEL = {};

SARIEL.ASSETSPATH = '/static/sarielmode/'

SARIEL.config = {
    usernames: true,
    modifyImages: true,
    header_hue_shift: true,
    dog: true,
    follower: true
}

SARIEL.functions = [];
SARIEL.addFunction = (name, func) => {
    if (!SARIEL.config[name]) return;
    SARIEL.functions.push(func);
}

SARIEL.addFunction("usernames", () => {
    const usernames = [...document.querySelectorAll(".username-coloured")].map(u => {
        return {
            seed: Math.random(),
            elm: u
        }
    });
    const update = () => {
        usernames.forEach(u => {
            noise.seed(u.seed);
            const t = Date.now();
            const x = noise.simplex3(t/5000, 0, 0) * 8;
            const y = noise.simplex3(0, t/5000 + u.seed/3, 0) * 8;
            const r = noise.simplex3(0, 0, t/3000 + u.seed) * 5;
            u.elm.style.transform = `translate(${x}px, ${y}px) rotate(${r}deg)`;
        })
        requestAnimationFrame(update);
    }
    update();
})

SARIEL.addFunction("modifyImages", () => {
    const tree = document.querySelector("[src*='tree_xmas']");
    tree.src = SARIEL.ASSETSPATH + "miku.gif";
    
    const banner = document.querySelector("[src*='utf_logo']");
    banner.src = SARIEL.ASSETSPATH + "new_header.png";

    const thread_images = document.querySelectorAll("[src*='read/normal'], [src*='read/locked'], [src*='unread/normal'], [src*='unread/locked']");
    thread_images.forEach(i => {
        const r = Math.floor(Math.random() * 360 / 90) * 90;
        i.style.transform = `rotate(${r}deg)`
    })
})

SARIEL.addFunction("header_hue_shift", () => {
    const menu = document.querySelector(".mainmenu");
    const update = () => {
        const t = (Date.now() / 10) % (360);
        menu.style.filter = `hue-rotate(${t}deg)`;
        requestAnimationFrame(update);
    }
    update();
})

SARIEL.addFunction("dog", () => {
    const addDog = () => {
        const seed = Math.random();
        const dog = new Image();
        dog.src = SARIEL.ASSETSPATH + "dog.gif";
        dog.classList.add("dougan");

        let oldX = 0;

        const update = () => {
            const t = Date.now();
            noise.seed(seed);
            const x = (noise.simplex3(t/5000, seed, 0) * 100 + 100) / 2;
            const y = (noise.simplex3(seed, t/5000, 0) * 100 + 100) / 2;

            const sign = Math.sign(x - oldX);
            dog.style.transform = `translate(-50%, -50%) scaleX(${-sign})`;
            oldX = x;

            dog.style.top = `${y}%`;
            dog.style.left = `${x}%`;
            requestAnimationFrame(update);
        }
        update();
        
        document.body.appendChild(dog);
    }

    const dog = new Image();
    dog.src = SARIEL.ASSETSPATH + "dog.gif";
    dog.id="dogbtn";
    dog.style.top = 0;
    dog.style.right = 0;

    dog.addEventListener("click", addDog);

    document.body.appendChild(dog);
})

SARIEL.addFunction("follower", () => {
    const noiseOverlay = document.createElement("div");
    noiseOverlay.id = "noise-overlay";
    document.body.appendChild(noiseOverlay);

    const follower = new Image();
    follower.id = "follower";
    const setFollowerImg = (name) => follower.src = `${SARIEL.ASSETSPATH}follower/${name}.png`;
    setFollowerImg("far")
    
    const pos = {x:-128, y:-128};
    const mouse = {x:0, y:0};
    document.addEventListener("mousemove", e => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    })

    const update = () => {
        const ang = Math.atan2(mouse.y - pos.y, mouse.x - pos.x);
        pos.x = pos.x + Math.cos(ang) * 0.5,
        pos.y = pos.y + Math.sin(ang) * 0.5;

        follower.style.left = `${pos.x}px`;
        follower.style.top = `${pos.y}px`;

        const dist = Math.sqrt((mouse.x - pos.x) ** 2 + (mouse.y - pos.y) ** 2);
        if (dist < 256) setFollowerImg("close");
        else if (dist < 512) setFollowerImg("near");
        else setFollowerImg("far");

        const rx = Math.random() * 256;
        const ry = Math.random() * 256;

        noiseOverlay.style.backgroundPosition = `${rx}px ${ry}px`;
        const o = constrain(map(dist, 256, 0, 0, 1), 0, 1);
        noiseOverlay.style.opacity = o;

        requestAnimationFrame(update);
    }
    update();
    document.body.appendChild(follower);
});

SARIEL.run = () => {
    document.addEventListener(
    "DOMContentLoaded", 
    ()=>SARIEL.functions.forEach(f=>f())
    );
}

SARIEL.run();