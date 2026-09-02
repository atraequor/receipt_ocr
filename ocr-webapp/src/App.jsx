import { useState } from "react"

function App() {
  const [image, setImage] = useState(null)

  function handleImageUpload(event) {
    const file = event.target.files[0]

    if (file) {
      setImage(file)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
      <div className="w-full max-w-xl px-6">

        <div className="text-center">
          <h1 className="text-5xl font-bold">
            OCR Reader
          </h1>

          <p className="mt-4 text-zinc-400">
            Read your receipts.
          </p>
        </div>

        <label className="mt-10 block cursor-pointer rounded-2xl border-2 border-dashed border-zinc-700 p-12 text-center hover:border-cyan-400 transition">
          
          <p className="text-lg">
            📄 Drop your image here
          </p>

          <p className="mt-2 text-sm text-zinc-500">
            or click to browse
          </p>

          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />

        </label>

        {image && (
          <div className="mt-6">
            <p className="mb-3 text-sm text-zinc-400">
            Selected image
            </p>

            <img
              src={URL.createObjectURL(image)}
              alt="Selected"
              className="w-full max-h-80 object-contain rounded-xl border border-zinc-800"
            />

            <p className="mt-3 text-center text-sm text-cyan-400">
              {image.name}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App