"use strict";

//JS
import { d2Get, d2PostJson, d2PutJson } from "./js/d2api.js";
import Choices from "choices.js";
import M from "materialize-css";

//CSS
import "./css/style.css";
import "materialize-css/dist/css/materialize.min.css";
import "choices.js/public/assets/styles/choices.min.css";

// Initialize Choices.js instances globally
let userRolesSelectInstance;
let additionalAuthoritiesSelectInstance;
let existingRolesSelectInstance;
let modifyRolesSelectInstance;

const defaultAuthorities = ["F_USER_ADD", "F_USER_DELETE", "M_dhis-web-user", "F_USER_VIEW"];

function showToast(message, success = true) {
    M.toast({ html: message, classes: success ? "green" : "red" });
}


document.addEventListener("DOMContentLoaded", () => {
    // Initialize Materialize tabs
    const elems = document.querySelectorAll(".tabs");
    M.Tabs.init(elems);

    // Initialize Choices.js instances
    userRolesSelectInstance = new Choices("#userRoles", {
        removeItemButton: true,
        searchEnabled: true,
        itemSelectText: "",
        shouldSort: false,
        dropdownPosition: "auto"
    });

    additionalAuthoritiesSelectInstance = new Choices("#additionalAuthorities", {
        removeItemButton: true,
        searchEnabled: true,
        itemSelectText: "",
        shouldSort: false,
        dropdownPosition: "auto"
    });

    existingRolesSelectInstance = new Choices("#existingRoles", {
        searchEnabled: true,
        itemSelectText: "",
        shouldSort: false,
        dropdownPosition: "auto"
    });

    modifyRolesSelectInstance = new Choices("#modifyRoles", {
        removeItemButton: true,
        searchEnabled: true,
        itemSelectText: "",
        shouldSort: false,
        dropdownPosition: "auto"
    });

    // Fetch user roles and authorities on load
    populateUserRoles(userRolesSelectInstance);
    populateAuthorities(additionalAuthoritiesSelectInstance);
    populateExistingRoles(existingRolesSelectInstance);
});



async function populateUserRoles(choicesInstance) {
    try {
        const response = await d2Get("/api/userRoles?paging=false");
        const userRoles = response.userRoles;
        const userRolesOptions = userRoles.map(role => ({ value: role.id, label: role.displayName }));
        choicesInstance.clearStore(); // Clear existing choices
        choicesInstance.setChoices(userRolesOptions, "value", "label", true);
    } catch (error) {
        console.error("Failed to fetch user roles", error);
        showToast("Failed to fetch user roles", false);
    }
}



async function populateAuthorities(choicesInstance) {
    try {
        const response = await d2Get("/api/authorities");
        const authorities = response.systemAuthorities;

        // Map authorities returning 'selected' flag for the defaultAuthorities
        const authoritiesOptions = authorities.map(auth => ({
            value: auth.id,
            label: auth.name,
            selected: defaultAuthorities.includes(auth.id)
        }));

        choicesInstance.clearChoices(); // Clear existing choices
        choicesInstance.setChoices(authoritiesOptions, "value", "label", true);
    } catch (error) {
        console.error("Failed to fetch authorities", error);
    }
}



async function populateExistingRoles(choicesInstance) {
    try {
        const response = await d2Get("/api/userRoles?paging=false");
        const userRoles = response.userRoles;
        const userRolesOptions = userRoles.map(role => ({ value: role.id, label: role.displayName }));
        choicesInstance.clearStore(); // Clear existing choices
        choicesInstance.setChoices(userRolesOptions, "value", "label", true);
    } catch (error) {
        console.error("Failed to fetch existing roles", error);
        showToast("Failed to fetch existing roles", false);
    }
}



window.createNewUserRole = async function () {
    const roleName = document.getElementById("newRoleName").value;
    const selectedUserRoles = Array.from(document.getElementById("userRoles").selectedOptions).map(option => option.value);
    const selectedAuthorities = Array.from(document.getElementById("additionalAuthorities").selectedOptions).map(option => option.value);

    try {
        const rolesToManage = await Promise.all(selectedUserRoles.map(id => d2Get(`/api/userRoles/${id}?fields=:owner`)));
        const aggregatedAuthorities = new Set(selectedAuthorities);

        rolesToManage.forEach(role => {
            role.authorities.forEach(auth => aggregatedAuthorities.add(auth));
        });

        const newRole = {
            name: roleName,
            description: `Admin role for managing users with roles: ${selectedUserRoles.join(", ")}`,
            authorities: Array.from(aggregatedAuthorities)
        };

        await d2PostJson("/api/userRoles", newRole);
        showToast("User role created successfully!");
    } catch (error) {
        console.error("Failed to create user role", error);
        showToast("Failed to create user role. Check console for details.", false);
    }
};


// Function to validate and modify an existing user role
window.validateUserRole = async function () {
    const existingRoleId = document.getElementById("existingRoles").value;

    try {
        const validatedRole = await d2Get(`/api/userRoles/${existingRoleId}?fields=:owner`);
        const validatedRoleAuthorities = new Set(validatedRole.authorities);

        const allRolesResponse = await d2Get("/api/userRoles?fields=:owner&paging=false");
        const allRoles = allRolesResponse.userRoles;

        const manageableRoles = allRoles.filter(role => {
            if (role.id === existingRoleId) return false;
            if (!role.authorities) return false;
            return role.authorities.every(auth => validatedRoleAuthorities.has(auth));
        });

        const managedRoleNames = manageableRoles.map(role => role.name);
        const managedRoleIds = manageableRoles.map(role => role.id);

        populateManagedRoles(managedRoleNames);
        populateModifyRolesSelect(allRoles, managedRoleIds.concat(existingRoleId));

        document.getElementById("validationResults").style.display = "block";
    } catch (error) {
        console.error("Failed to validate user role", error);
        showToast("Failed to validate user role. Check console for details.", false);
    }
};



async function populateManagedRoles(managedRoleNames) {
    const managedRolesList = document.getElementById("managedRolesList");
    managedRolesList.innerHTML = managedRoleNames.map(roleName => `<li>${roleName}</li>`).join("");
}

async function populateModifyRolesSelect(allRoles, excludeRoleIds) {
    const selectableRoles = allRoles.filter(role => !excludeRoleIds.includes(role.id));
    modifyRolesSelectInstance.clearChoices(); // Clear existing choices
    modifyRolesSelectInstance.setChoices(selectableRoles.map(role => ({ value: role.id, label: role.name })), "value", "label", true);
}



window.modifyUserRole = async function () {
    const existingRoleId = document.getElementById("existingRoles").value;
    const modifiedRoles = Array.from(document.getElementById("modifyRoles").selectedOptions).map(option => option.value);

    try {
        const role = await d2Get(`/api/userRoles/${existingRoleId}?fields=:owner`);
        const aggregatedAuthorities = new Set(role.authorities);

        const rolesToManage = await Promise.all(modifiedRoles.map(id => d2Get(`/api/userRoles/${id}?fields=:owner`)));
        rolesToManage.forEach(role => {
            role.authorities.forEach(auth => aggregatedAuthorities.add(auth));
        });

        const updatedRole = {
            ...role,
            authorities: Array.from(aggregatedAuthorities)
        };

        await d2PutJson(`/api/userRoles/${existingRoleId}`, updatedRole);
        showToast("User role updated successfully!");
    } catch (error) {
        console.error("Failed to modify user role", error);
        showToast("Failed to modify user role. Check console for details.", false);
    }
};

