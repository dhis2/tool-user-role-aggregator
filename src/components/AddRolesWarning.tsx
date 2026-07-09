import i18n from '@dhis2/d2-i18n'
import { NoticeBox } from '@dhis2/ui'
import React from 'react'
import styles from './AddRolesWarning.module.css'

/**
 * Warning shown when the current user lacks the authorities needed to
 * create or update user roles (F_USERROLE_PRIVATE_ADD / F_USERROLE_PUBLIC_ADD).
 */
export const AddRolesWarning = ({
    canAddUserRoles,
}: {
    canAddUserRoles: boolean
}) => {
    if (canAddUserRoles) {
        return null
    }
    return (
        <div className={styles.notice}>
            <NoticeBox warning title={i18n.t('Missing permissions')}>
                {i18n.t(
                    'You do not have permission to create or update user roles.'
                )}
            </NoticeBox>
        </div>
    )
}
