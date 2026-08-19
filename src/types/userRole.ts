export interface UserRole {
    id: string
    displayName: string
    authorities?: string[]
}

export interface SystemAuthority {
    id: string
    name: string
}

/** The special authority that grants superuser access to everything */
export const AUTHORITY_ALL = 'ALL'

/**
 * A role is manageable by someone holding `heldAuthorities` when every
 * authority of the role is included in the held set (the DHIS2 user
 * management rule: you may only manage users with equal or fewer
 * privileges than yourself).
 */
export const canManageRole = (
    heldAuthorities: ReadonlySet<string>,
    role: UserRole
): boolean => {
    if (heldAuthorities.has(AUTHORITY_ALL)) {
        return true
    }
    const roleAuthorities = role.authorities ?? []
    if (roleAuthorities.includes(AUTHORITY_ALL)) {
        return false
    }
    return roleAuthorities.every((authority) => heldAuthorities.has(authority))
}

/**
 * Whether a user holding `heldAuthorities` may grant `authorityId` — a
 * superuser (holder of `ALL`) implicitly holds every authority. Used to
 * limit the authority picker to the current user's own authorities.
 */
export const canGrantAuthority = (
    heldAuthorities: ReadonlySet<string>,
    authorityId: string
): boolean =>
    heldAuthorities.has(AUTHORITY_ALL) || heldAuthorities.has(authorityId)
