// Replace with your API Gateway base URL and API key
const apiBaseUrl = "https://arvc6smbml.execute-api.us-east-1.amazonaws.com/v1"; // API Gateway base URL
const apiKey = "AyN0bf9hGB77uprDnfpPF3bilg3uU9AO9n9UrC7B"; // Replace with your actual API key

// Function to search for photos
async function searchPhotos(query) {
    const url = `${apiBaseUrl}/search?q=${encodeURIComponent(query)}`;
    try {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "x-api-key": apiKey
            }
        });

        if (!response.ok) {
            console.error("Failed to search photos:", await response.text());
            alert("Failed to search photos.");
            return;
        }

        const data = await response.json();

        // Expecting the API to return an array of results with URLs and labels
        if (data.results && Array.isArray(data.results)) {
            displaySearchResults(data.results);
        } else {
            console.error("Unexpected response structure:", data);
            alert("Unexpected response structure.");
        }
    } catch (error) {
        console.error("Error during photo search:", error);
        alert("An error occurred while searching photos.");
    }
}

// Display search results
function displaySearchResults(results) {
    const resultsDiv = document.getElementById("searchResults");
    resultsDiv.innerHTML = ""; // Clear previous results

    if (!results || results.length === 0) {
        resultsDiv.innerHTML = "<p>No photos found.</p>";
        return;
    }

    results.forEach(photo => {
        const photoDiv = document.createElement("div");
        const img = document.createElement("img");

        // Use the photo URL provided by the API
        img.src = photo.url || "https://via.placeholder.com/200"; // Fallback to placeholder
        img.alt = "Photo";
        img.style.width = "200px";
        img.style.height = "200px";

        const labels = document.createElement("p");
        labels.textContent = `Labels: ${photo.labels.join(", ")}`;

        photoDiv.appendChild(img);
        photoDiv.appendChild(labels);
        resultsDiv.appendChild(photoDiv);
    });
}

// Function to upload a photo
async function uploadPhoto(file, customLabels) {
    const objectName = encodeURIComponent(file.name);
    const url = `${apiBaseUrl}/photos/${objectName}`;

    try {
        console.log("Uploading file:", {
            fileName: file.name,
            fileType: file.type,
            fileSize: file.size,
        });

        const response = await fetch(url, {
            method: "PUT",
            headers: {
                "x-api-key": apiKey, // API key for authorization
                "x-amz-meta-customLabels": customLabels,
                "Content-Type": file.type || "application/octet-stream", // Ensure correct MIME type
            },
            body: file, // Raw binary file data
        });

        if (response.ok) {
            console.log("Upload successful:", await response.text());
            alert("Photo uploaded successfully!");
        } else {
            console.error("Upload failed:", await response.text());
            alert("Failed to upload photo. Please check the console for more details.");
        }
    } catch (error) {
        console.error("Error during photo upload:", error);
        alert("An error occurred during photo upload.");
    }
}

// Event listeners for forms
document.getElementById("searchForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = document.getElementById("query").value;
    await searchPhotos(query);
});

document.getElementById("uploadForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const fileInput = document.getElementById("photo");
    const customLabels = document.getElementById("customLabels").value;

    if (!fileInput.files.length) {
        alert("Please select a photo to upload.");
        return;
    }

    const file = fileInput.files[0];
    await uploadPhoto(file, customLabels);
});
