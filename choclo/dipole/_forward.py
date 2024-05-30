# Copyright (c) 2022 The Choclo Developers.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
#
# This code is part of the Fatiando a Terra project (https://www.fatiando.org)
#
import numpy as np
from numba import jit

from ..constants import VACUUM_MAGNETIC_PERMEABILITY


@jit(nopython=True)
def magnetic_field(
    easting_p,
    northing_p,
    upward_p,
    easting_q,
    northing_q,
    upward_q,
    magnetic_moment_east,
    magnetic_moment_north,
    magnetic_moment_up,
):
    r"""
    Magnetic field due to a dipole

    Returns the three components of the magnetic field due to a single dipole
    a single computation point.

    .. note::

        Use this function when all the three component of the magnetic fields
        are needed. Running this function is faster than computing each
        component separately. Use one of :func:`magnetic_e`,
        :func:`magnetic_n`, :func:`magnetic_u` if you need only one of them.

    Parameters
    ----------
    easting_p : float
        Easting coordinate of the observation point in meters.
    northing_p : float
        Northing coordinate of the observation point in meters.
    upward_p : float
        Upward coordinate of the observation point in meters.
    easting_q : float
        Easting coordinate of the dipole in meters.
    northing_q : float
        Northing coordinate of the dipole in meters.
    upward_q : float
        Upward coordinate of the dipole in meters.
    magnetic_moment_east : float
        The East component of the magnetic moment vector of the dipole. Must be
        in :math:`A m^2`.
    magnetic_moment_north : float
        The North component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.
    magnetic_moment_up : float
        The upward component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.

    Returns
    -------
    b_e : float
        Easting component of the magnetic field generated by the dipole
        on the observation point in :math:`\text{T}`.
    b_n : float
        Northing component of the magnetic field generated by the dipole
        on the observation point in :math:`\text{T}`.
    b_u : float
        Upward component of the magnetic field generated by the dipole
        on the observation point in :math:`\text{T}`.

    Notes
    -----
    Returns the three components of the magnetic field
    :math:`\mathbf{B}` on the observation point
    :math:`\mathbf{p} = (x_p, y_p, z_p)` generated by a single dipole located
    in :math:`\mathbf{q} = (x_q, y_q, z_q)` and magnetic moment
    :math:`\mathbf{m}=(m_x, m_y, m_z)`.

    .. math::

        \mathbf{B}(\mathbf{p}) =
            \frac{\mu_0}{4\pi}
            \left[
            \frac{
                3 (\mathbf{m} \cdot \mathbf{r}) \mathbf{r}
            }{
                \lVert r \rVert^5
            }
            -
            \frac{
                \mathbf{m}
            }{
                \lVert r \rVert^3
            }
            \right]

    where :math:`\mathbf{r} = \mathbf{p} - \mathbf{q}`,
    :math:`\lVert \cdot \rVert` refer to the :math:`L_2` norm
    and :math:`\mu_0` is the vacuum magnetic permeability.
    """
    r_e = easting_p - easting_q
    r_n = northing_p - northing_q
    r_u = upward_p - upward_q
    distance = np.sqrt(r_e**2 + r_n**2 + r_u**2)
    dotproduct = (
        magnetic_moment_east * r_e
        + magnetic_moment_north * r_n
        + magnetic_moment_up * r_u
    )
    c_m = VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi
    b_e = c_m * (
        3 * dotproduct * r_e / distance**5 - magnetic_moment_east / distance**3
    )
    b_n = c_m * (
        3 * dotproduct * r_n / distance**5 - magnetic_moment_north / distance**3
    )
    b_u = c_m * (3 * dotproduct * r_u / distance**5 - magnetic_moment_up / distance**3)
    return b_e, b_n, b_u


@jit(nopython=True)
def magnetic_e(
    easting_p,
    northing_p,
    upward_p,
    easting_q,
    northing_q,
    upward_q,
    magnetic_moment_east,
    magnetic_moment_north,
    magnetic_moment_up,
):
    r"""
    Easting component of the magnetic field due to a dipole

    Returns the easting component of the magnetic field by a single dipole on
    a single computation point

    Parameters
    ----------
    easting_p : float
        Easting coordinate of the observation point in meters.
    northing_p : float
        Northing coordinate of the observation point in meters.
    upward_p : float
        Upward coordinate of the observation point in meters.
    easting_q : float
        Easting coordinate of the dipole in meters.
    northing_q : float
        Northing coordinate of the dipole in meters.
    upward_q : float
        Upward coordinate of the dipole in meters.
    magnetic_moment_east : float
        The East component of the magnetic moment vector of the dipole. Must be
        in :math:`A m^2`.
    magnetic_moment_north : float
        The North component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.
    magnetic_moment_up : float
        The upward component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.

    Returns
    -------
    b_e : float
        Easting component of the magnetic field generated by the dipole
        on the observation point in :math:`\text{T}`.

    Notes
    -----
    Returns the easting component :math:`B_x(\mathbf{p})` of the magnetic field
    :math:`\mathbf{B}` on the observation point
    :math:`\mathbf{p} = (x_p, y_p, z_p)` generated by a single dipole located
    in :math:`\mathbf{q} = (x_q, y_q, z_q)` and magnetic moment
    :math:`\mathbf{m}=(m_x, m_y, m_z)`.

    .. math::

        B_x(\mathbf{p}) =
            \frac{\mu_0}{4\pi}
            \left[
            \frac{
                3 (\mathbf{m} \cdot \mathbf{r}) x
            }{
                \lVert r \rVert^5
            }
            -
            \frac{
                m_x
            }{
                \lVert r \rVert^3
            }
            \right]

    where :math:`\mathbf{r} = \mathbf{p} - \mathbf{q}`,
    :math:`\lVert \cdot \rVert` refer to the :math:`L_2` norm
    and :math:`\mu_0` is the vacuum magnetic permeability.
    """
    r_e = easting_p - easting_q
    r_n = northing_p - northing_q
    r_u = upward_p - upward_q
    distance = np.sqrt(r_e**2 + r_n**2 + r_u**2)
    dotproduct = (
        magnetic_moment_east * r_e
        + magnetic_moment_north * r_n
        + magnetic_moment_up * r_u
    )
    result = 3 * dotproduct * r_e / distance**5 - magnetic_moment_east / distance**3
    return VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi * result


@jit(nopython=True)
def magnetic_n(
    easting_p,
    northing_p,
    upward_p,
    easting_q,
    northing_q,
    upward_q,
    magnetic_moment_east,
    magnetic_moment_north,
    magnetic_moment_up,
):
    r"""
    Northing component of the magnetic field due to a dipole

    Returns the northing component of the magnetic field by a single dipole on
    a single computation point

    Parameters
    ----------
    easting_p : float
        Easting coordinate of the observation point in meters.
    northing_p : float
        Northing coordinate of the observation point in meters.
    upward_p : float
        Upward coordinate of the observation point in meters.
    easting_q : float
        Easting coordinate of the dipole in meters.
    northing_q : float
        Northing coordinate of the dipole in meters.
    upward_q : float
        Upward coordinate of the dipole in meters.
    magnetic_moment_east : float
        The East component of the magnetic moment vector of the dipole. Must be
        in :math:`A m^2`.
    magnetic_moment_north : float
        The North component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.
    magnetic_moment_up : float
        The upward component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.

    Returns
    -------
    b_n : float
        Northing component of the magnetic field generated by the dipole on the
        observation point in :math:`\text{T}`.

    Notes
    -----
    Returns the northing component :math:`B_y(\mathbf{p})` of the magnetic
    field :math:`\mathbf{B}` on the observation point
    :math:`\mathbf{p} = (x_p, y_p, z_p)` generated by a single dipole located
    in :math:`\mathbf{q} = (x_q, y_q, z_q)` and magnetic moment
    :math:`\mathbf{m}=(m_x, m_y, m_z)`.

    .. math::

        B_y(\mathbf{p}) =
            \frac{\mu_0}{4\pi}
            \left[
            \frac{
                3 (\mathbf{m} \cdot \mathbf{r}) y
            }{
                \lVert r \rVert^5
            }
            -
            \frac{
                m_y
            }{
                \lVert r \rVert^3
            }
            \right]

    where :math:`\mathbf{r} = \mathbf{p} - \mathbf{q}`,
    :math:`\lVert \cdot \rVert` refer to the :math:`L_2` norm
    and :math:`\mu_0` is the vacuum magnetic permeability.
    """
    r_e = easting_p - easting_q
    r_n = northing_p - northing_q
    r_u = upward_p - upward_q
    distance = np.sqrt(r_e**2 + r_n**2 + r_u**2)
    dotproduct = (
        magnetic_moment_east * r_e
        + magnetic_moment_north * r_n
        + magnetic_moment_up * r_u
    )
    result = 3 * dotproduct * r_n / distance**5 - magnetic_moment_north / distance**3
    return VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi * result


@jit(nopython=True)
def magnetic_u(
    easting_p,
    northing_p,
    upward_p,
    easting_q,
    northing_q,
    upward_q,
    magnetic_moment_east,
    magnetic_moment_north,
    magnetic_moment_up,
):
    r"""
    Upward component of the magnetic field due to a dipole

    Returns the upward component of the magnetic field by a single dipole on
    a single computation point

    Parameters
    ----------
    easting_p : float
        Easting coordinate of the observation point in meters.
    northing_p : float
        Northing coordinate of the observation point in meters.
    upward_p : float
        Upward coordinate of the observation point in meters.
    easting_q : float
        Easting coordinate of the dipole in meters.
    northing_q : float
        Northing coordinate of the dipole in meters.
    upward_q : float
        Upward coordinate of the dipole in meters.
    magnetic_moment_east : float
        The East component of the magnetic moment vector of the dipole. Must be
        in :math:`A m^2`.
    magnetic_moment_north : float
        The North component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.
    magnetic_moment_up : float
        The upward component of the magnetic moment vector of the dipole. Must
        be in :math:`A m^2`.

    Returns
    -------
    b_u : float
        Upward component of the magnetic field generated by the dipole on the
        observation point in :math:`\text{T}`.

    Notes
    -----
    Returns the upward component :math:`B_z(\mathbf{p})` of the magnetic
    field :math:`\mathbf{B}` on the observation point
    :math:`\mathbf{p} = (x_p, y_p, z_p)` generated by a single dipole located
    in :math:`\mathbf{q} = (x_q, y_q, z_q)` and magnetic moment
    :math:`\mathbf{m}=(m_x, m_y, m_z)`.

    .. math::

        B_z(\mathbf{p}) =
            \frac{\mu_0}{4\pi}
            \left[
            \frac{
                3 (\mathbf{m} \cdot \mathbf{r}) z
            }{
                \lVert r \rVert^5
            }
            -
            \frac{
                m_z
            }{
                \lVert r \rVert^3
            }
            \right]

    where :math:`\mathbf{r} = \mathbf{p} - \mathbf{q}`,
    :math:`\lVert \cdot \rVert` refer to the :math:`L_2` norm
    and :math:`\mu_0` is the vacuum magnetic permeability.
    """
    r_e = easting_p - easting_q
    r_n = northing_p - northing_q
    r_u = upward_p - upward_q
    distance = np.sqrt(r_e**2 + r_n**2 + r_u**2)
    dotproduct = (
        magnetic_moment_east * r_e
        + magnetic_moment_north * r_n
        + magnetic_moment_up * r_u
    )
    result = 3 * dotproduct * r_u / distance**5 - magnetic_moment_up / distance**3
    return VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi * result
