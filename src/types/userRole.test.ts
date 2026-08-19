import {
    AUTHORITY_ALL,
    canGrantAuthority,
    canManageRole,
    UserRole,
} from './userRole'

const role = (authorities?: string[]): UserRole => ({
    id: 'r1',
    displayName: 'Role',
    authorities,
})

describe('canManageRole', () => {
    it('allows a superuser (ALL) to manage any role', () => {
        const held = new Set([AUTHORITY_ALL])
        expect(canManageRole(held, role(['F_ANYTHING']))).toBe(true)
        expect(canManageRole(held, role([AUTHORITY_ALL]))).toBe(true)
        expect(canManageRole(held, role(undefined))).toBe(true)
    })

    it('allows managing a role whose authorities are a subset of the held set', () => {
        const held = new Set(['F_A', 'F_B', 'F_C'])
        expect(canManageRole(held, role(['F_A']))).toBe(true)
        expect(canManageRole(held, role(['F_A', 'F_C']))).toBe(true)
    })

    it('rejects a role with an authority the holder lacks', () => {
        const held = new Set(['F_A', 'F_B'])
        expect(canManageRole(held, role(['F_A', 'F_X']))).toBe(false)
    })

    it('rejects a superuser role for non-superuser holders', () => {
        const held = new Set(['F_A', 'F_B'])
        expect(canManageRole(held, role([AUTHORITY_ALL]))).toBe(false)
        expect(canManageRole(held, role([AUTHORITY_ALL, 'F_A']))).toBe(false)
    })

    it('treats a role without authorities as manageable by anyone', () => {
        const held = new Set<string>()
        expect(canManageRole(held, role(undefined))).toBe(true)
        expect(canManageRole(held, role([]))).toBe(true)
    })
})

describe('canGrantAuthority', () => {
    it('lets a superuser (ALL) grant any authority', () => {
        const held = new Set([AUTHORITY_ALL])
        expect(canGrantAuthority(held, 'F_ANYTHING')).toBe(true)
        expect(canGrantAuthority(held, AUTHORITY_ALL)).toBe(true)
    })

    it('lets a user grant an authority they hold', () => {
        expect(canGrantAuthority(new Set(['F_A', 'F_B']), 'F_A')).toBe(true)
    })

    it('rejects an authority the user does not hold', () => {
        expect(canGrantAuthority(new Set(['F_A']), 'F_B')).toBe(false)
        expect(canGrantAuthority(new Set(['F_A']), AUTHORITY_ALL)).toBe(false)
        expect(canGrantAuthority(new Set<string>(), 'F_A')).toBe(false)
    })
})
