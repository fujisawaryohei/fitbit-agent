"use client";

import Script from "next/script";

export default function Eruda() {
  return (
    <Script
      src="//cdn.jsdelivr.net/npm/eruda"
      strategy="afterInteractive"
      onLoad={() => {
        // @ts-expect-error eruda is a global
        window.eruda?.init();
      }}
    />
  );
}
