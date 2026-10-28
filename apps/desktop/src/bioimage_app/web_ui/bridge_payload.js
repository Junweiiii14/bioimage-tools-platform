'use strict';

/**
 * Shared desktop identity. This is a static producer contract; Python validates
 * incoming requests independently. No measurement or file contents belong here.
 * @typedef {{projectId: string, sessionEpoch: number, revision: number}} WorkbenchIdentity
 */

/**
 * @typedef {WorkbenchIdentity & {
 *   schema_version: 1,
 *   requestId: string,
 *   operation: string,
 *   value: Record<string, unknown>
 * }} AdvancedRequest
 */

/**
 * Keep the established wire keys, version and property order. The caller owns
 * transport, pending state and size checks; this function only creates the data.
 * @param {WorkbenchIdentity} identity
 * @param {string} requestId
 * @param {string} operation
 * @param {Record<string, unknown>} value
 * @returns {AdvancedRequest}
 */
function makeAdvancedRequest(identity, requestId, operation, value) {
    return {
        schema_version: 1,
        requestId,
        projectId: identity.projectId,
        sessionEpoch: identity.sessionEpoch,
        revision: identity.revision,
        operation,
        value,
    };
}
