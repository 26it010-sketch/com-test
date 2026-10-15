import client from "./client";

export const listDocuments = () =>
    client.get("/documents").then((r) => r.data);

export const uploadDocument = (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);

    return client
        .post("/documents", form, {
            onUploadProgress: (e) =>
                e.total &&
                onProgress?.(
                    Math.round((e.loaded / e.total) * 100)
                ),
        })
        .then((r) => r.data);
};

export const deleteDocument = (id) =>
    client.delete(`/documents/${id}`);

// Fetch PDFs with the Authorization header and return a blob.
export const fetchDocumentBlob = async (id) => {
    const token = localStorage.getItem("dm_token");

    const response = await fetch(
        `/api/documents/${id}/file`,
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
            cache: "no-store",
        }
    );

    if (!response.ok) {
        throw new Error(`PDF request failed: ${response.status}`);
    }

    const blob = await response.blob();

    console.log("PDF downloaded:", {
        size: blob.size,
        type: blob.type,
    });

    return blob;
};