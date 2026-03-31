/**
 * Comprime una imagen client-side usando Canvas API.
 * - Resize si cualquier dimensión supera MAX_DIM (1920px), manteniendo aspect ratio
 * - PNG > 500 KB se convierte a WEBP para mejor compresión
 * - Quality 0.85
 */

const MAX_DIM = 1920;
const QUALITY = 0.85;
const WEBP_THRESHOLD = 500 * 1024; // 500 KB

export function compressImage(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);

      let { width, height } = img;
      if (width > MAX_DIM || height > MAX_DIM) {
        const ratio = Math.min(MAX_DIM / width, MAX_DIM / height);
        width = Math.round(width * ratio);
        height = Math.round(height * ratio);
      }

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas 2D context not available'));
        return;
      }
      ctx.drawImage(img, 0, 0, width, height);

      const useWebp = file.type === 'image/png' && file.size > WEBP_THRESHOLD;
      const outputType = useWebp ? 'image/webp' : file.type;

      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Image compression failed'));
          }
        },
        outputType,
        QUALITY,
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error('Failed to load image'));
    };

    img.src = objectUrl;
  });
}

/** Returns the MIME-appropriate extension for the compressed output. */
export function compressedExtension(file: File): string {
  if (file.type === 'image/png' && file.size > WEBP_THRESHOLD) return '.webp';
  const ext = file.name.split('.').pop()?.toLowerCase() ?? 'jpg';
  return `.${ext}`;
}
