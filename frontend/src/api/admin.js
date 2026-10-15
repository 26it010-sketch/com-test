import client from "./client";

export const listUsers = () =>
    client.get("/admin/users").then((r) => r.data);

export const setUserActive = (id, is_active) =>
    client.patch(`/admin/users/${id}`, { is_active })
        .then((r) => r.data);

export const listAllDocuments = (ownerId) =>
    client.get("/admin/documents", {
        params: ownerId ? { owner_id: ownerId } : {},
    }).then((r) => r.data);

export const deleteAnyDocument = (id) =>
    client.delete(`/admin/documents/${id}`);

export const fetchAnyDocumentBlob = async (id) => {
    const token = localStorage.getItem("dm_token");

    const response = await fetch(
        `/api/admin/documents/${id}/file`,
        {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
            },
            cache: "no-store",
        }
    );

    if (!response.ok) {
        const message = await response.text();
        throw new Error(
            `Admin PDF request failed: ${response.status} ${message}`
        );
    }

    const blob = await response.blob();

    console.log("Admin PDF downloaded:", {
        size: blob.size,
        type: blob.type,
    });

    return blob;
};