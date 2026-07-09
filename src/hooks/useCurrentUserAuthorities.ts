import { useMemo } from 'react'
import { AUTHORITY_ALL } from '@/types/userRole'
import { useApiDataQuery } from '@/utils/useApiDataQuery'

interface Me {
    authorities: string[]
}

/**
 * The current user's granted authorities, plus derived permission flags
 * for working with user roles.
 */
export const useCurrentUserAuthorities = () => {
    const { data, isLoading, error } = useApiDataQuery<Me>({
        queryKey: ['me', 'authorities'],
        query: {
            resource: 'me',
            params: {
                fields: 'authorities',
            },
        },
        cacheTime: Infinity,
        staleTime: Infinity,
    })

    const authorities = useMemo(() => new Set(data?.authorities ?? []), [data])

    const isSuperuser = authorities.has(AUTHORITY_ALL)
    const canAddUserRoles =
        isSuperuser ||
        authorities.has('F_USERROLE_PRIVATE_ADD') ||
        authorities.has('F_USERROLE_PUBLIC_ADD')

    return {
        authorities,
        isSuperuser,
        canAddUserRoles,
        isLoading,
        error,
    }
}
