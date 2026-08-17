import React, { useMemo } from "react";

interface Star {
  id: number;
  top: string;
  left: string;
  size: number;
  opacity: number;
  duration: string;
  delay: string;
}

interface DustParticle {
  id: number;
  top: string;
  left: string;
  size: number;
  color: string;
  duration: string;
  delay: string;
}

export function StarfieldBackground() {
  // Generate static star coordinates once
  const stars: Star[] = useMemo(() => {
    const arr: Star[] = [];
    for (let i = 0; i < 70; i++) {
      const size = Math.random() < 0.6 ? 1 : Math.random() < 0.9 ? 2 : 3;
      arr.push({
        id: i,
        top: `${(Math.random() * 100).toFixed(2)}%`,
        left: `${(Math.random() * 100).toFixed(2)}%`,
        size,
        opacity: +(0.25 + Math.random() * 0.75).toFixed(2),
        duration: `${(2.2 + Math.random() * 4.5).toFixed(2)}s`,
        delay: `${(Math.random() * 5).toFixed(2)}s`,
      });
    }
    return arr;
  }, []);

  // Floating wandering cosmic dust
  const dustParticles: DustParticle[] = useMemo(() => {
    const colors = [
      "rgba(56, 189, 248, 0.4)",  // cyan
      "rgba(251, 191, 36, 0.35)",  // amber
      "rgba(147, 197, 253, 0.4)",  // light blue
      "rgba(167, 139, 250, 0.35)", // soft violet
    ];
    const arr: DustParticle[] = [];
    for (let i = 0; i < 12; i++) {
      arr.push({
        id: i,
        top: `${(10 + Math.random() * 80).toFixed(2)}%`,
        left: `${(5 + Math.random() * 90).toFixed(2)}%`,
        size: Math.floor(2 + Math.random() * 4),
        color: colors[i % colors.length],
        duration: `${(14 + Math.random() * 16).toFixed(2)}s`,
        delay: `${(Math.random() * 8).toFixed(2)}s`,
      });
    }
    return arr;
  }, []);

  return (
    <div className="starfield-universe" aria-hidden="true">
      {/* 1. Deep Nebular Breathing Aurora Gradients */}
      <div className="nebula-cloud nebula-1" />
      <div className="nebula-cloud nebula-2" />
      <div className="nebula-cloud nebula-3" />

      {/* 2. Twinkling & Dimming Stars */}
      <div className="stars-layer">
        {stars.map((star) => (
          <span
            key={star.id}
            className="twinkle-star"
            style={{
              top: star.top,
              left: star.left,
              width: `${star.size}px`,
              height: `${star.size}px`,
              opacity: star.opacity,
              animationDuration: star.duration,
              animationDelay: star.delay,
            }}
          />
        ))}
      </div>

      {/* 3. Wandering Cosmic Dust Drift */}
      <div className="dust-layer">
        {dustParticles.map((dust) => (
          <span
            key={dust.id}
            className="wandering-dust"
            style={{
              top: dust.top,
              left: dust.left,
              width: `${dust.size}px`,
              height: `${dust.size}px`,
              backgroundColor: dust.color,
              boxShadow: `0 0 ${dust.size * 3}px ${dust.color}`,
              animationDuration: dust.duration,
              animationDelay: dust.delay,
            }}
          />
        ))}
      </div>

      {/* 4. Shooting Stars / Meteors */}
      <span className="shooting-meteor meteor-1" />
      <span className="shooting-meteor meteor-2" />
      <span className="shooting-meteor meteor-3" />
    </div>
  );
}
