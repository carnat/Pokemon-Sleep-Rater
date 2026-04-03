/**
 * OCR via Google Cloud Vision REST API.
 *
 * Ported from ocr.py — calls the Vision API text_detection endpoint
 * using a simple API key (no service account needed).
 */

/**
 * Detect text in an image at the given URL using Google Cloud Vision API.
 *
 * @param imageUrl - Public URL of the image to analyse.
 * @param apiKey - Google Cloud API key with Vision API enabled.
 * @returns Array of text lines extracted from the image, or null on failure.
 */
export async function detectTextUri(
  imageUrl: string,
  apiKey: string
): Promise<string[] | null> {
  const body = {
    requests: [
      {
        image: { source: { imageUri: imageUrl } },
        features: [{ type: "TEXT_DETECTION" }],
      },
    ],
  };

  const res = await fetch(
    `https://vision.googleapis.com/v1/images:annotate?key=${encodeURIComponent(apiKey)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );

  if (!res.ok) {
    console.error(`Vision API error: ${res.status} ${res.statusText}`);
    return null;
  }

  const data = (await res.json()) as {
    responses: Array<{
      textAnnotations?: Array<{ description: string }>;
      error?: { message: string };
    }>;
  };

  const response = data.responses?.[0];
  if (response?.error) {
    console.error(`Vision API error: ${response.error.message}`);
    return null;
  }

  const fullText = response?.textAnnotations?.[0]?.description;
  if (!fullText) return null;

  // Strip "Lv. X" prefixes (same regex as Python version)
  const pattern = /.*?L[vV]\. ?\d+ /;
  return fullText.split("\n").map((line) => line.replace(pattern, ""));
}
