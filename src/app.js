"use strict";

import "materialize-css";
import M from "materialize-css";

//JS
import { d2Get, d2PostJson, d2PutJson } from "./js/d2api.js";

//CSS
import "./css/header.css";
import "./css/style.css";


// Initialize Materialize components
document.addEventListener('DOMContentLoaded', () => {
    const elems = document.querySelectorAll('select');
    M.FormSelect.init(elems);

    // Fetch user roles and authorities onload
    populateUserRoles();
    populateAuthorities();
    populateExistingRoles();
});


async function populateUserRoles() {
    try {
        const response = await d2Get("/api/userRoles");
        const userRoles = response.userRoles;
        const userRolesSelect = document.getElementById("userRoles");
        userRolesSelect.innerHTML = userRoles.map(role => `<option value="${role.id}">${role.displayName}</option>`).join('');
        M.FormSelect.init(userRolesSelect);
    } catch (error) {
        console.error("Failed to fetch user roles", error);
    }
}




async function populateAuthorities() {
    try {
        const response = await d2Get("/api/authorities");
        const authorities = response.systemAuthorities;
        const additionalAuthoritiesSelect = document.getElementById("additionalAuthorities");
        additionalAuthoritiesSelect.innerHTML = authorities.map(auth => `<option value="${auth.id}">${auth.name}</option>`).join('');
        M.FormSelect.init(additionalAuthoritiesSelect);
    } catch (error) {
        console.error("Failed to fetch authorities", error);
    }
}







async function populateExistingRoles() {
    try {
        const response = await d2Get("/api/userRoles");
        const userRoles = response.userRoles;
        const existingRolesSelect = document.getElementById("existingRoles");
        existingRolesSelect.innerHTML = userRoles.map(role => `<option value="${role.id}">${role.displayName}</option>`).join('');
        M.FormSelect.init(existingRolesSelect);
    } catch (error) {
        console.error("Failed to fetch existing roles", error);
    }
}


function createCheckboxList(items, namePrefix) {
    if (!Array.isArray(items)) {
        return '';
    }
    return items.map((item, idx) => `
        <label>
            <input type="checkbox" class="filled-in" id="${namePrefix}_${idx}" value="${item.id || item}">
            <span>${item.displayName || item}</span>
        </label>
    `).join('');
}



// Function to create a new user role
window.createNewUserRole = async function () {
    const roleName = document.getElementById("newRoleName").value;
    const selectedUserRoles = Array.from(document.getElementById("userRoles").selectedOptions).map(option => option.value);
    const selectedAuthorities = Array.from(document.getElementById("additionalAuthorities").selectedOptions).map(option => option.value);

    try {
        const rolesToManage = await Promise.all(selectedUserRoles.map(id => d2Get(`/api/userRoles/${id}`)));
        const aggregatedAuthorities = new Set(selectedAuthorities);

        rolesToManage.forEach(role => {
            role.authorities.forEach(auth => aggregatedAuthorities.add(auth));
        });

        const newRole = {
            name: roleName,
            description: `Admin role for managing users with roles: ${selectedUserRoles.join(', ')}`,
            authorities: Array.from(aggregatedAuthorities)
        };

        await d2PostJson("/api/userRoles", newRole);
        alert("User role created successfully!");
    } catch (error) {
        console.error("Failed to create user role", error);
        alert("Failed to create user role. Check console for details.");
    }
};





// Function to validate and modify an existing user role
window.validateUserRole = async function () {
    const existingRoleId = document.getElementById("existingRoles").value;

    try {
        const response = await d2Get(`/api/userRoles/${existingRoleId}?fields=:owner`);
        const existingRole = response;
        populateManagedRoles(existingRole.authorities);
        document.getElementById("validationResults").style.display = "block";
    } catch (error) {
        console.error("Failed to validate user role", error);
    }
};


async function populateManagedRoles(authorities) {
    const managedRolesList = document.getElementById("managedRolesList");
    managedRolesList.innerHTML = authorities.map(auth => `<li>${auth}</li>`).join('');

    const modifyRolesSelect = document.getElementById("modifyRoles");
    try {
        const response = await d2Get("/api/userRoles");
        const userRoles = response.userRoles;
        modifyRolesSelect.innerHTML = userRoles.map(role => `<option value="${role.id}">${role.displayName}</option>`).join('');
        M.FormSelect.init(modifyRolesSelect);
    } catch (error) {
        console.error("Failed to fetch user roles for modification", error);
    }
}



window.modifyUserRole = async function () {
    const existingRoleId = document.getElementById("existingRoles").value;
    const modifiedRoles = Array.from(document.getElementById("modifyRoles").selectedOptions).map(option => option.value);

    try {
        const role = await d2Get(`/api/userRoles/${existingRoleId}`);
        const aggregatedAuthorities = new Set(role.authorities);

        const rolesToManage = await Promise.all(modifiedRoles.map(id => d2Get(`/api/userRoles/${id}`)));
        rolesToManage.forEach(role => {
            role.authorities.forEach(auth => aggregatedAuthorities.add(auth));
        });

        const updatedRole = {
            ...role,
            authorities: Array.from(aggregatedAuthorities)
        };

        await d2PutJson(`/api/userRoles/${existingRoleId}`, updatedRole);
        alert("User role updated successfully!");
    } catch (error) {
        console.error("Failed to modify user role", error);
        alert("Failed to modify user role. Check console for details.");
    }
};

