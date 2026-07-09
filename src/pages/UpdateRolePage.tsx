import i18n from '@dhis2/d2-i18n'
import {
    Button,
    ButtonStrip,
    CircularLoader,
    NoticeBox,
    SingleSelectField,
    SingleSelectOption,
    Transfer,
} from '@dhis2/ui'
import React, { useMemo, useState } from 'react'
import styles from './UpdateRolePage.module.css'
import { AddRolesWarning } from '@/components/AddRolesWarning'
import { useAddAuthoritiesToRole } from '@/hooks/useAddAuthoritiesToRole'
import { useCurrentUserAuthorities } from '@/hooks/useCurrentUserAuthorities'
import { useUserRoles } from '@/hooks/useUserRoles'
import { canManageRole } from '@/types/userRole'

export const UpdateRolePage = () => {
    const {
        canAddUserRoles,
        isLoading: isLoadingMe,
        error: meError,
    } = useCurrentUserAuthorities()
    const {
        userRoles,
        isLoading: isLoadingRoles,
        error: rolesError,
    } = useUserRoles()

    const [selectedRoleId, setSelectedRoleId] = useState<string>()
    const [roleIdsToAdd, setRoleIdsToAdd] = useState<string[]>([])

    const { addAuthoritiesToRole, isUpdating } = useAddAuthoritiesToRole({
        onSuccess: () => setRoleIdsToAdd([]),
    })

    const selectedRole = userRoles?.find((role) => role.id === selectedRoleId)

    const { managedRoles, candidateRoles } = useMemo(() => {
        if (!userRoles || !selectedRole) {
            return { managedRoles: [], candidateRoles: [] }
        }
        const heldAuthorities = new Set(selectedRole.authorities ?? [])
        const otherRoles = userRoles.filter(
            (role) => role.id !== selectedRole.id
        )
        return {
            managedRoles: otherRoles.filter((role) =>
                canManageRole(heldAuthorities, role)
            ),
            candidateRoles: otherRoles.filter(
                (role) => !canManageRole(heldAuthorities, role)
            ),
        }
    }, [userRoles, selectedRole])

    if (isLoadingMe || isLoadingRoles) {
        return (
            <div className={styles.loadingContainer}>
                <CircularLoader />
            </div>
        )
    }

    const error = meError || rolesError
    if (error || !userRoles) {
        return (
            <NoticeBox error title={i18n.t('Error loading data')}>
                {error?.message || i18n.t('An unknown error occurred')}
            </NoticeBox>
        )
    }

    const onSubmit = () => {
        if (!selectedRole || roleIdsToAdd.length === 0) {
            return
        }
        addAuthoritiesToRole({
            roleId: selectedRole.id,
            roleIdsToAdd,
        })
    }

    return (
        <div className={styles.card}>
            <h1 className={styles.title}>
                {i18n.t('Update existing user role')}
            </h1>
            <p className={styles.description}>
                {i18n.t(
                    'Select an existing role to see which user roles it can currently manage, and extend it with the authorities of additional roles so its members can manage users with those roles as well.'
                )}
            </p>
            <AddRolesWarning canAddUserRoles={canAddUserRoles} />
            <div className={styles.field}>
                <SingleSelectField
                    className={styles.roleSelect}
                    label={i18n.t('Existing role')}
                    selected={selectedRoleId}
                    onChange={({ selected }) => {
                        setSelectedRoleId(selected)
                        setRoleIdsToAdd([])
                    }}
                    filterable
                    noMatchText={i18n.t('No roles match the filter')}
                >
                    {userRoles.map((role) => (
                        <SingleSelectOption
                            key={role.id}
                            label={role.displayName}
                            value={role.id}
                        />
                    ))}
                </SingleSelectField>
            </div>
            {selectedRole && (
                <>
                    <h2 className={styles.sectionTitle}>
                        {i18n.t('User roles that can be managed')}
                    </h2>
                    {managedRoles.length > 0 ? (
                        <ul className={styles.managedRolesList}>
                            {managedRoles.map((role) => (
                                <li key={role.id}>{role.displayName}</li>
                            ))}
                        </ul>
                    ) : (
                        <p className={styles.emptyText}>
                            {i18n.t(
                                'This role cannot manage any other user roles yet.'
                            )}
                        </p>
                    )}
                    <h2 className={styles.sectionTitle}>
                        {i18n.t('Add managed roles')}
                    </h2>
                    {candidateRoles.length > 0 ? (
                        <>
                            <div className={styles.field}>
                                <span className={styles.fieldLabel}>
                                    {i18n.t(
                                        'The authorities of the selected roles will be added to {{role}}',
                                        {
                                            role: selectedRole.displayName,
                                        }
                                    )}
                                </span>
                                <Transfer
                                    options={candidateRoles.map((role) => ({
                                        label: role.displayName,
                                        value: role.id,
                                    }))}
                                    selected={roleIdsToAdd}
                                    onChange={({ selected }) =>
                                        setRoleIdsToAdd(selected)
                                    }
                                    filterable
                                    filterablePicked
                                    height="280px"
                                />
                            </div>
                            <ButtonStrip>
                                <Button
                                    primary
                                    onClick={onSubmit}
                                    loading={isUpdating}
                                    disabled={
                                        !canAddUserRoles ||
                                        isUpdating ||
                                        roleIdsToAdd.length === 0
                                    }
                                >
                                    {i18n.t('Add authorities to role')}
                                </Button>
                            </ButtonStrip>
                        </>
                    ) : (
                        <p className={styles.emptyText}>
                            {i18n.t(
                                'This role can already manage all other user roles.'
                            )}
                        </p>
                    )}
                </>
            )}
        </div>
    )
}
